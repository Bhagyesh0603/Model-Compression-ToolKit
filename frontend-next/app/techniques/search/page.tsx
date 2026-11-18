import type { Metadata } from 'next';
import { search, mb, ms, pct } from '@/src/data/results';
import { LadderReplay } from '@/src/explore/LadderReplay';
import { Provenance } from '@/src/site/Provenance';
import { Figure, Section } from '@/src/site/Section';
import { TechniqueShell } from '@/src/site/TechniqueShell';

export const metadata: Metadata = { title: 'Budget search — compresskit' };

const LADDER = [
  ['Quantize only', 'No retraining. Often enough.'],
  ['Mixed precision', 'Keep the most sensitive layers in FP32, when accuracy is the only gap and the host has fast INT8.'],
  ['Quantization-aware training', 'A short recovery pass, when accuracy is the only gap.'],
  ['Prune when needed', 'Explore pruning ratios only when latency or size fails, protecting fragile layers.'],
  ['Distill when needed', 'Recover accuracy with or without pruning; accuracy-only failures can skip pruning.'],
] as const;

export default function SearchPage() {
  return (
    <TechniqueShell
      slug="search"
      title="State a budget, search for a measured fit"
      lede={
        <p>
          You write what you need, for example <span className="font-mono text-[15px]">accuracy_drop&lt;1%,size&lt;5mb</span>.
          The search starts with the cheapest option and escalates only when it falls short, and stops at the first
          configuration that fits. This is a bounded search, not a guarantee of the globally smallest change.
          Here accuracy_drop&lt;1% means a drop of one percentage point.
        </p>
      }
    >
      <Section
        title="Conditional search stages"
        lede={
          <p>
            These are conditional branches, not steps that every run executes. Pruning is skipped when only accuracy fails. Stopping early is the point. A pipeline that always runs every stage spends hours fine-tuning to solve a
            problem quantization had already solved, and gives back accuracy it never needed to lose.
          </p>
        }
      >
        <ol className="grid gap-px overflow-hidden rounded-[22px] border border-(--line) bg-(--line) md:grid-cols-5">
          {LADDER.map(([name, body], i) => (
            <li key={name} className="bg-(--bg) p-5">
              <p className="text-[12px] text-(--muted)">Step {i + 1}</p>
              <p className="mt-1 text-[17px] leading-tight tracking-[-0.02em]">{name}</p>
              <p className="mt-2 text-[13px] leading-snug text-(--muted)">{body}</p>
            </li>
          ))}
        </ol>
      </Section>

      <Section tone="dark"
        title="Three recorded searches"
        lede={
          <p>
            Same ResNet-20, three budgets. One is met by quantization alone, one needs pruning and recovery, and one
            cannot be met, in which case the search returns the best trade-off it actually measured rather than a
            number it didn&apos;t.
          </p>
        }
      >
        <Figure caption={`During the search, accuracy is measured on a 2000-image subset and latency over fewer timed runs to keep the loop affordable. The chosen configuration is re-measured in full before it is reported, so a baseline can read slightly differently between searches.`}>
          <LadderReplay />
          <Provenance p={search.provenance as never} />
        </Figure>
      </Section>
    </TechniqueShell>
  );
}
