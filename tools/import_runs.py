"""Recover results.json-shaped records from runs that only left a report or a log behind.

Two sources are supported, both written by compresskit itself:

* the standalone HTML report (`compresskit pipeline --report report.html`), and
* the printed pipeline log saved in a notebook's output cells.

Every value is read from the source; nothing is estimated. What a source does
not contain stays None (the HTML report has no MAC counts; the log has no
per-layer channels or per-class recall). The HTML report prints recall to one
decimal place, so recall recovered from it carries that rounding.

    python tools/import_runs.py            # writes artifacts/imported/*.json
"""
from __future__ import annotations

import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "imported"
CIFAR10 = ["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]


# --------------------------------------------------------------------------- HTML report
class _Tables(HTMLParser):
    """Collect each <h2> section's tables (rows of cell text), its <li> items and the cards/kv pairs."""

    def __init__(self):
        super().__init__()
        self.section = "_top"
        self.sections: dict[str, dict] = {}
        self._buf: list[str] | None = None
        self._row: list[str] | None = None
        self._tag_stack: list[tuple[str, str]] = []
        self.subtitles: list[str] = []
        self.cards: list[dict] = []
        self.kv: dict[str, str] = {}
        self._dt: str | None = None

    def _sec(self) -> dict:
        return self.sections.setdefault(self.section, {"rows": [], "items": []})

    def handle_starttag(self, tag, attrs):
        cls = dict(attrs).get("class", "") or ""
        self._tag_stack.append((tag, cls))
        if tag in ("h2", "td", "th", "li", "dt", "dd", "p") or (tag == "div" and cls.split()[:1] in (["label"], ["value"], ["note"])):
            self._buf = []
        if tag == "tr":
            self._row = []
        if tag == "div" and cls == "card":
            self.cards.append({})

    def handle_endtag(self, tag):
        tag_open, cls = self._tag_stack.pop() if self._tag_stack else (tag, "")
        text = " ".join("".join(self._buf or []).split()) if self._buf is not None else None
        if tag == "h2" and text is not None:
            self.section = text
        elif tag in ("td", "th") and self._row is not None and text is not None:
            self._row.append(text)
        elif tag == "tr" and self._row is not None:
            self._sec()["rows"].append(self._row)
            self._row = None
        elif tag == "li" and text is not None:
            self._sec()["items"].append(text)
        elif tag == "p" and cls == "sub" and text is not None:
            self.subtitles.append(text)
        elif tag == "div" and cls.split()[:1] in (["label"], ["value"], ["note"]) and self.cards and text is not None:
            self.cards[-1][cls.split()[0]] = text
        elif tag == "dt" and text is not None:
            self._dt = text
        elif tag == "dd" and text is not None and self._dt:
            self.kv[self._dt] = text
        if tag in ("h2", "td", "th", "li", "dt", "dd", "p") or tag == "div":
            self._buf = None if tag != "div" or cls.split()[:1] in (["label"], ["value"], ["note"]) else self._buf

    def handle_data(self, data):
        if self._buf is not None:
            self._buf.append(data)


def _num(s: str) -> float:
    return float(s.replace(",", "").replace("%", "").replace("x", "").strip())


def parse_report_html(path: Path) -> dict:
    doc = path.read_text(encoding="utf-8")
    # The report's own table cells never contain markup, so a light parser is enough.
    t = _Tables()
    t.feed(doc)

    stage_rows = [r for r in t.sections["Per-stage measurements"]["rows"] if r and r[0] != "stage"]

    def stage(r: list[str]) -> dict:
        name, precision, top1, _dpp, med, p95, _speed, size, params = r
        return {
            "stage": name, "precision": precision, "accuracy": round(_num(top1) / 100, 6),
            "latency": {"median_ms": _num(med), "p95_ms": _num(p95)},
            "size_mb": _num(size), "parameters": int(_num(params)), "notes": "",
            "artifact": f"{name}.onnx",
        }

    baseline, *stages = [stage(r) for r in stage_rows]

    history = []
    for r in t.sections.get("Gradual pruning schedule", {}).get("rows", []):
        if r[0] == "step":
            continue
        history.append({
            "step": int(r[0]), "params": int(_num(r[1])),
            "acc_after_cut": round(_num(r[2]) / 100, 6), "acc_after_finetune": round(_num(r[3]) / 100, 6),
        })

    channels = {}
    for r in t.sections.get("Channels per layer", {}).get("rows", []):
        if r[0] == "layer":
            continue
        channels[r[0]] = [int(r[1]), int(r[2])]

    per_class = {}
    for key, sec in t.sections.items():
        if key.startswith("Per-class accuracy"):
            for r in sec["rows"]:
                if r[0] == "class":
                    continue
                per_class[r[0]] = (int(r[1]), _num(r[2]) / 100, _num(r[3]) / 100)
    if per_class:
        assert sorted(per_class) == sorted(CIFAR10), f"unexpected classes in {path}: {sorted(per_class)}"
        support = [per_class[c][0] for c in CIFAR10]
        baseline["class_metrics"] = {"recall": [round(per_class[c][1], 4) for c in CIFAR10], "support": support}
        stages[-1]["class_metrics"] = {"recall": [round(per_class[c][2], 4) for c in CIFAR10], "support": support}

    caveat_prefix = ("Latency was measured on", "The INT8 model was built on")
    notes = t.sections.get("Notes", {}).get("items", [])
    warnings = [n for n in notes if not n.startswith(caveat_prefix)]

    cards = {c.get("label"): c for c in t.cards}
    speedup = _num(cards["latency"]["note"].split("x vs")[0])
    size_reduction = _num(cards["size"]["note"].split("x vs")[0])
    efficiency = _num(cards["efficiency score"]["value"])

    cpu_line = t.kv.get("cpu", "")
    m = re.match(r"(.*) \((\d+) logical, (\d+) performance\)", cpu_line)
    versions = dict(re.findall(r"(\w+) ([^,]+)", t.kv.get("versions", "")))
    machine = re.search(r"·\s*(\S+)\s*·\s*generated", t.subtitles[0]) if t.subtitles else None
    generated = re.search(r"generated (\d{4}-\d{2}-\d{2})", t.subtitles[0]) if t.subtitles else None
    host = {
        "system": None,
        "machine": machine.group(1) if machine else None,
        "cpu": m.group(1) if m else cpu_line,
        "logical_cores": int(m.group(2)) if m else None,
        "performance_cores": int(m.group(3)) if m else None,
        "features": [f.strip() for f in t.kv.get("ISA features", "").split(",") if f.strip()],
        "int8_speed": t.kv.get("INT8 kernels"),
        "versions": versions,
    }
    quant_text = t.kv.get("quantization", "")
    qm = re.match(r"(\w+)(?:, (\d+)% of compute ops)?", quant_text)
    quantization = {"precision": qm.group(1), "coverage": int(qm.group(2)) / 100 if qm.group(2) else None,
                    "quantized_ops": {}} if qm else None

    return {
        "_source": {"kind": "html-report", "file": path.name, "generated": generated.group(1) if generated else None},
        "host": host,
        "baseline": baseline,
        "stages": stages,
        "prune_stats": {
            "params_before": baseline["parameters"], "params_after": stages[-1]["parameters"],
            "macs_before": None, "macs_after": None,
            "ratio_requested": None, "steps": len(history), "channels": channels,
        } if channels else None,
        "prune_history": history,
        "quantization": quantization,
        "totals": {
            "accuracy_drop_pp": round((baseline["accuracy"] - stages[-1]["accuracy"]) * 100, 4),
            "speedup": speedup, "size_reduction": size_reduction, "efficiency_score": efficiency,
        },
        "warnings": warnings,
    }


# --------------------------------------------------------------------------- pipeline log
STAGE_LINE = re.compile(
    r"^(\S+)\s+(fp32|fp16|int8)\s+acc\s+([\d.]+)%\s+lat\s+([\d.]+) ms \(p95\s+([\d.]+)\)\s+size\s+([\d.]+) MB\s+params\s+([\d,]+)",
    re.M,
)


def parse_pipeline_log(text: str, *, source: str) -> dict:
    rows = {}
    for m in STAGE_LINE.finditer(text):
        rows[m.group(1)] = {  # the summary table repeats each line; the last copy wins, they are identical
            "stage": m.group(1), "precision": m.group(2), "accuracy": round(float(m.group(3)) / 100, 6),
            "latency": {"median_ms": float(m.group(4)), "p95_ms": float(m.group(5))},
            "size_mb": float(m.group(6)), "parameters": int(m.group(7).replace(",", "")), "notes": "",
            "artifact": f"{m.group(1)}.onnx",
        }
    baseline = rows.pop("baseline")
    stages = list(rows.values())

    history = []
    for m in re.finditer(r"\[step (\d+)\] accuracy ([\d.]+)% after cut -> ([\d.]+)% after fine-tune", text):
        history.append({"step": int(m.group(1)), "params": None,
                        "acc_after_cut": round(float(m.group(2)) / 100, 6),
                        "acc_after_finetune": round(float(m.group(3)) / 100, 6)})

    pm = re.search(r"params ([\d,]+) -> ([\d,]+) \([\d.]+% removed\)\s+MACs ([\d.]+)M -> ([\d.]+)M", text)
    steps = re.search(r"--steps (\d+)", text)
    ratio = re.search(r"--prune ([\d.]+)", text)

    host_m = re.search(r"host\s+: (.*) \((\S+), (\S+)\)", text)
    cores = re.search(r"cores\s+: (\d+) logical / (\d+) performance", text)
    isa = re.search(r"ISA\s+: (.*)", text)
    int8 = re.search(r"INT8\s+: (\w+)", text)
    vers = re.search(r"versions\s+: (.*)", text)
    host = {
        "system": host_m.group(3) if host_m else None,
        "machine": host_m.group(2) if host_m else None,
        "cpu": host_m.group(1) if host_m else None,
        "logical_cores": int(cores.group(1)) if cores else None,
        "performance_cores": int(cores.group(2)) if cores else None,
        "features": [f.strip() for f in isa.group(1).split(",")] if isa else [],
        "int8_speed": int8.group(1) if int8 else None,
        "versions": dict(re.findall(r"(\w+) ([^,]+)", vers.group(1))) if vers else {},
    }
    q = re.search(r"quantized (\d+)/(\d+) compute ops", text)

    tm = re.search(r"latency\s+[\d.]+ -> [\d.]+ ms\s+\(([\d.]+)x\)", text)
    sm = re.search(r"size\s+[\d.]+ -> [\d.]+ MB\s+\(([\d.]+)x\)", text)
    em = re.search(r"efficiency ([\d.]+)", text)
    warnings = sorted({w.strip() for w in re.findall(r"^\s*! (.*)$", text, re.M)}, key=text.find)

    return {
        "_source": {"kind": "pipeline-log", "file": source},
        "host": host,
        "baseline": baseline,
        "stages": stages,
        "prune_stats": {
            "params_before": int(pm.group(1).replace(",", "")), "params_after": int(pm.group(2).replace(",", "")),
            "macs_before": float(pm.group(3)) * 1e6, "macs_after": float(pm.group(4)) * 1e6,
            "ratio_requested": float(ratio.group(1)) if ratio else None,
            "steps": int(steps.group(1)) if steps else len(history), "channels": {},
        } if pm else None,
        "prune_history": history,
        "quantization": {"precision": "int8", "coverage": int(q.group(1)) / int(q.group(2)), "quantized_ops": {}} if q else None,
        "totals": {
            "accuracy_drop_pp": round((baseline["accuracy"] - stages[-1]["accuracy"]) * 100, 4),
            "speedup": float(tm.group(1)), "size_reduction": float(sm.group(1)),
            "efficiency_score": float(em.group(1)),
        },
        "warnings": warnings,
    }


def notebook_text(path: Path) -> str:
    nb = json.loads(path.read_text(encoding="utf-8"))
    parts = []
    for cell in nb["cells"]:
        if cell.get("cell_type") == "code":
            parts.append("".join(cell.get("source", "")))
        for out in cell.get("outputs", []):
            parts.append("".join(out.get("text", "")) or "".join(out.get("data", {}).get("text/plain", "")))
    return html.unescape("\n".join(parts))


# --------------------------------------------------------------------------- main
IMPORTS = [
    ("resnet20_intel_i5", lambda: parse_report_html(ROOT / "runs" / "resnet20_intel_i5_report.html")),
    ("resnet56_intel_i5", lambda: parse_report_html(ROOT / "runs" / "resnet56_intel_i5_report.html")),
    ("resnet56_kaggle", lambda: parse_pipeline_log(notebook_text(ROOT / "runs" / "resnet56_kaggle_run.ipynb"),
                                                   source="runs/resnet56_kaggle_run.ipynb")),
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in IMPORTS:
        record = fn()
        path = OUT / f"{name}.json"
        path.write_text(json.dumps(record, indent=1))
        b, f, t = record["baseline"], record["stages"][-1], record["totals"]
        print(f"{path.relative_to(ROOT)}: {b['accuracy']:.2%} -> {f['accuracy']:.2%}, "
              f"{t['size_reduction']}x smaller, {t['speedup']}x faster, {len(record['stages'])} stages, "
              f"{len(record['prune_history'])} prune steps")
    return 0


if __name__ == "__main__":
    sys.exit(main())
