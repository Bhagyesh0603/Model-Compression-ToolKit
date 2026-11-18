import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { Suspense } from 'react';
import { ArrowLeft, ChevronDown, Download } from 'lucide-react';
import { distillation, finalStage, mb, modelBySlug, models, ms, pct, ratio, slugOf, count, type ModelRecord } from '@/src/data/results';
import { PageFrame } from '@/src/site/PageFrame';
import { Provenance } from '@/src/site/Provenance';
import { Figure, Section, Wrap } from '@/src/site/Section';
import { ChannelBars } from '@/src/site/charts/ChannelBars';
import { ParetoMini } from '@/src/site/charts/ParetoMini';
import { PlayedSawtooth } from '@/src/explore/PlayedSawtooth';
import { StageExplorer } from '@/src/explore/StageExplorer';
import { StripReplay } from '@/src/explore/StripReplay';
import { Band } from '@/src/motion/Band';
import { Reveal } from '@/src/landing/Motion';
import { DATASET_INTRO, GLOSSARY, MODEL_INTRO, STEP_GUIDE, outOf100 } from '@/src/site/modelGuide';
import { BeforeAfter } from '@/src/site/models/BeforeAfter';
import { ClassChange } from '@/src/site/models/ClassChange';
import { DotGrid } from '@/src/site/models/DotGrid';
import { RunsCompare } from '@/src/site/models/RunsCompare';

export function generateStaticParams() {
  return models.map((m) => ({ slug: slugOf(m.arch) }));
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params;
  const m = modelBySlug(slug);
  return { title: m ? `${m.name} compressed — compresskit` : 'Model — compresskit' };
}

const machineOf = (m: ModelRecord) => m.runs.find((r) => r.primary)?.machine ?? m.provenance.host;

function mistakesLine(dropPoints: number): string {
  const n = Math.round(dropPoints);
  if (n <= 0) return 'Fewer than one extra mistake in every 100 photos.';
  return `Roughly ${n} more mistake${n === 1 ? '' : 's'} in every 100 photos than the original.`;
}

function Disclosure({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <details className="group rounded-[24px] border border-(--line) p-5 sm:p-8">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-4 text-[15px] [&::-webkit-details-marker]:hidden">
        {label}
        <ChevronDown className="h-4 w-4 shrink-0 transition-transform group-open:rotate-180" aria-hidden="true" />
      </summary>
      <div className="mt-6">{children}</div>
    </details>
  );
}

async function ModelBody({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const m = modelBySlug(slug);
  if (!m) notFound();
  const b = m.baseline;
  const f = finalStage(m);
  const t = m.totals;
  const intro = MODEL_INTRO[m.arch];
  const machine = machineOf(m);
  const slowInt8 = m.host.int8_speed === 'slow';
  const ps = m.prune_stats;
  const channelRows = ps ? Object.entries(ps.channels).map(([name, [before, after]]) => ({ name, before, after })) : [];
  const classNames = m.dataset === 'CIFAR-10' ? distillation.classes : null;
  const perClass =
    classNames && b.recall && f.recall
      ? classNames
          .map((name, i) => ({ name, before: b.recall![i], after: f.recall![i] }))
          .sort((x, y) => x.after - x.before - (y.after - y.before))
      : null;
  const stagesByKey = Object.fromEntries(m.stages.map((s) => [s.stage, s]));
  const photos = m.test_images ? `${count(m.test_images)} test photos` : 'the test photos';

  return (
    <>
      {/* ------------------------------------------------------------------ header */}
      <Band tone="light" labelledBy="model-title">
        <Wrap className="pb-14 pt-16 sm:pb-20 sm:pt-24">
          <Reveal>
            <Link href="/models" className="inline-flex items-center gap-2 text-[14px] text-(--muted) transition-colors hover:text-(--fg)">
              <ArrowLeft className="h-4 w-4" aria-hidden="true" /> All models
            </Link>
            <div className="mt-8 flex flex-wrap gap-2 text-[12px]">
              {intro ? <span className="rounded-full bg-(--chip) px-3 py-1 text-(--chip-fg)">{intro.family}</span> : null}
              <span className="rounded-full bg-(--chip) px-3 py-1 text-(--chip-fg)">Dataset: {m.dataset}</span>
              <span className="rounded-full bg-(--chip) px-3 py-1 text-(--chip-fg)">
                Tested {m.runs.length === 1 ? 'once' : `${m.runs.length} times`}
              </span>
            </div>
            <h1 id="model-title" className="mt-5 max-w-[18ch] text-balance text-[clamp(40px,5.4vw,76px)] font-normal leading-[1.02] tracking-[-0.045em]">
              {m.name}
            </h1>
            <div className="mt-8 grid gap-8 lg:grid-cols-[1.3fr_1fr] lg:gap-16">
              <div className="space-y-4 text-[18px] leading-[1.65]">
                {intro ? (
                  <>
                    <p>{intro.what}</p>
                    <p className="text-(--muted)">{intro.why}</p>
                  </>
                ) : (
                  <p>{m.schedule}.</p>
                )}
              </div>
              {DATASET_INTRO[m.dataset] ? (
                <aside className="rounded-[24px] border border-(--line) p-6 text-[14px] leading-[1.7] text-(--muted)">
                  <p className="mb-2 text-[12px] uppercase tracking-[0.08em]">What it was tested on</p>
                  {DATASET_INTRO[m.dataset]}
                </aside>
              ) : null}
            </div>
          </Reveal>
        </Wrap>
      </Band>

      {/* ------------------------------------------------------------------ the short version */}
      <Section
        id="result"
        title="The short version"
        lede={
          <p className="text-[19px] leading-[1.6] text-(--fg)">
            We made {m.name} <strong className="font-medium">{ratio(t.size_reduction)} smaller</strong> and{' '}
            <strong className="font-medium">{ratio(t.speedup)} faster</strong>. It still labels{' '}
            <strong className="font-medium">{pct(f.accuracy)}</strong> of {photos} correctly, down from {pct(b.accuracy)}.
          </p>
        }
      >
        <div className="grid gap-4 lg:grid-cols-3">
          <BeforeAfter
            term="Accuracy"
            question="Does it still get the answer right?"
            before={b.accuracy}
            after={f.accuracy}
            beforeShown={pct(b.accuracy)}
            afterShown={pct(f.accuracy)}
            scaleMax={1}
            verdict={`${t.accuracy_drop_pp.toFixed(2)} points lower`}
            explain={mistakesLine(t.accuracy_drop_pp)}
          />
          <BeforeAfter
            term="File size"
            question="How much space does it take?"
            before={b.size_mb}
            after={f.size_mb}
            beforeShown={mb(b.size_mb)}
            afterShown={mb(f.size_mb)}
            verdict={`${ratio(t.size_reduction)} smaller`}
            explain="A smaller file downloads faster, fits on phones and small devices, and costs less to store and serve."
          />
          <BeforeAfter
            term="Latency (time per photo)"
            question="How fast does it answer?"
            before={b.median_ms}
            after={f.median_ms}
            beforeShown={ms(b.median_ms)}
            afterShown={ms(f.median_ms)}
            verdict={`${ratio(t.speedup)} faster`}
            explain={
              slowInt8
                ? `Timed on the ${machine}, which has no fast 8-bit maths. On a computer that does, the compressed model would gain more.`
                : `Timed on the ${machine}. Speed depends on the computer, so this is a statement about that machine.`
            }
          />
        </div>

        <div className="mt-4 rounded-[24px] border border-(--line) p-6 sm:p-8">
          <div className="grid gap-8 md:grid-cols-[1fr_auto_auto] md:items-center md:gap-14">
            <div>
              <h3 className="text-[20px] tracking-[-0.02em]">Out of every 100 photos</h3>
              <p className="mt-2 max-w-[46ch] text-[15px] leading-[1.65] text-(--muted)">
                These illustrative dots show the accuracy rate per 100 photos, not individual recorded predictions. Filled dots
                represent correct labels and hollow dots represent mistakes, rounded to whole photos.
              </p>
            </div>
            <DotGrid correct={outOf100(b.accuracy)} label="Original model" />
            <DotGrid correct={outOf100(f.accuracy)} label="Compressed model" accent />
          </div>
        </div>
        <Provenance p={m.provenance} source={m.source} />
      </Section>

      {/* ------------------------------------------------------------------ what we did */}
      <Section
        id="steps"
        title="What we did, step by step"
        lede={<p>This recorded run has three reported compression stages. After each one the model is measured again, so you can see what each step saved and what it cost.</p>}
      >
        <ol className="grid gap-4 lg:grid-cols-3">
          {STEP_GUIDE.map((step, i) => {
            const s = stagesByKey[step.key];
            const prev = i === 0 ? b : (stagesByKey[STEP_GUIDE[i - 1].key] ?? b);
            return (
              <li key={step.key} className="flex flex-col rounded-[24px] border border-(--line) p-6 sm:p-7">
                <div className="flex items-center gap-3">
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-(--inv-bg) text-[14px] text-(--inv-fg)">{i + 1}</span>
                  <span className="text-[12px] uppercase tracking-[0.08em] text-(--muted)">{step.term}</span>
                </div>
                <h3 className="mt-4 text-[21px] leading-tight tracking-[-0.02em]">{step.title}</h3>
                <p className="mt-3 text-[15px] leading-[1.65] text-(--muted)">{step.plain}</p>
                <p className="mt-3 border-l-2 border-(--line-strong) pl-3 text-[14px] italic leading-[1.6] text-(--muted)">{step.analogy}</p>
                {s ? (
                  <div className="mt-auto pt-6">
                    <p className="border-t border-(--line) pt-4 text-[12px] uppercase tracking-[0.08em] text-(--muted)">Measured after this step</p>
                    <dl className="figures-tab mt-3 grid grid-cols-3 gap-3 text-[13px]">
                      <div>
                        <dt className="text-(--muted)">Correct</dt>
                        <dd className="mt-1 text-[17px]">{pct(s.accuracy)}</dd>
                        <dd className="text-[11px] text-(--muted)">was {pct(prev.accuracy)}</dd>
                      </div>
                      <div>
                        <dt className="text-(--muted)">File</dt>
                        <dd className="mt-1 text-[17px]">{mb(s.size_mb)}</dd>
                        <dd className="text-[11px] text-(--muted)">was {mb(prev.size_mb)}</dd>
                      </div>
                      <div>
                        <dt className="text-(--muted)">Per photo</dt>
                        <dd className="mt-1 text-[17px]">{ms(s.median_ms)}</dd>
                        <dd className="text-[11px] text-(--muted)">was {ms(prev.median_ms)}</dd>
                      </div>
                    </dl>
                  </div>
                ) : null}
              </li>
            );
          })}
        </ol>
      </Section>

      <Section
        tone="dark"
        title="Try it: slide through the steps"
        lede={
          <p>
            Drag the slider from the original model to the finished one. On the right, each column is one layer of the model and
            each small block is one channel. Watch blocks disappear when it is pruned, and change colour when its numbers are
            rounded to 8 bits.
          </p>
        }
      >
        <StageExplorer fixedArch={m.arch} />
      </Section>

      {/* ------------------------------------------------------------------ test runs */}
      <Section
        id="runs"
        title={m.runs.length === 1 ? 'Tested once' : `Tested ${m.runs.length} times`}
        lede={
          <p>
            {m.runs.length === 1
              ? 'This model has one recorded test run so far.'
              : 'The same model went through the pipeline more than once, on different computers and with different settings. The numbers above come from the run marked "Shown on this page".'}
          </p>
        }
      >
        <RunsCompare runs={m.runs} />
      </Section>

      {/* ------------------------------------------------------------------ gradual pruning */}
      {m.prune_history.length > 0 ? (
        <Section
          title="Cutting a little at a time"
          lede={
            <p>
              The model was not cut all at once. It was trimmed in {m.prune_history.length} rounds. In each round accuracy drops
              sharply right after the cut (hollow dot), then climbs back most of the way after practice (filled dot). Cutting
              gradually lets the model recover each time instead of losing everything in one go.
            </p>
          }
        >
          <Figure caption={`${m.prune_history.length} rounds of cut, then practise. The line starts at the original accuracy, ${pct(b.accuracy)}.`}>
            <PlayedSawtooth
              baseline={b.accuracy}
              history={m.prune_history}
              className="w-full max-w-[720px]"
              summary={`Accuracy through ${m.prune_history.length} pruning rounds for ${m.name}`}
            />
          </Figure>
        </Section>
      ) : null}

      {/* ------------------------------------------------------------------ channels */}
      {ps && channelRows.length > 0 ? (
        <Section
          title="Where the model got thinner"
          lede={
            <p>
              {count(ps.params_before)} learned numbers became {count(ps.params_after)}. Each column below is one layer and each block
              in it is one channel. Grey blocks were removed; coloured blocks were kept.
            </p>
          }
        >
          <Figure caption="The recorded cut, replayed when this scrolls into view. Press Replay to watch it again.">
            <StripReplay arch={m.arch} />
          </Figure>
          <div className="mt-4">
            <Disclosure label={`Show the exact channel count for all ${channelRows.length} layers`}>
              <ChannelBars rows={channelRows} align={16} />
              <p className="mt-4 text-[13px] text-(--muted)">Pale bar: original width. Solid: kept. An asterisk marks a kept count that is not a multiple of 16.</p>
            </Disclosure>
          </div>
        </Section>
      ) : null}

      {/* ------------------------------------------------------------------ per class */}
      {perClass ? (
        <Section
          title="What it got worse at"
          lede={
            <p>
              The overall score hides where the model slipped, so here are the ten categories one by one. The compressed model lost
              the most on <strong className="font-medium text-(--fg)">{perClass[0].name}</strong> photos and the least on{' '}
              <strong className="font-medium text-(--fg)">{perClass[perClass.length - 1].name}</strong> photos.
            </p>
          }
        >
          <Figure caption="Share of each category's test photos labelled correctly, worst change first.">
            <ClassChange rows={perClass} />
          </Figure>
        </Section>
      ) : null}

      {/* ------------------------------------------------------------------ downloads */}
      {m.downloads && m.downloads.length > 0 ? (
        <Section
          title="Download the files"
          lede={<p>The actual model files from the {machine} run. They open in any ONNX viewer or runtime, such as Netron.</p>}
        >
          <ul className="flex flex-wrap gap-3">
            {m.downloads.map((d) => (
              <li key={d.href}>
                <a
                  href={d.href}
                  download
                  className="inline-flex h-12 items-center gap-3 rounded-full border border-(--line-strong) px-5 text-[14px] transition-colors hover:bg-(--hover)"
                >
                  <Download className="h-4 w-4" aria-hidden="true" />
                  {d.label}
                  <span className="text-(--muted)">{(d.size_bytes / 1e6).toFixed(2)} MB</span>
                </a>
              </li>
            ))}
          </ul>
        </Section>
      ) : null}

      {/* ------------------------------------------------------------------ glossary */}
      <Section id="glossary" title="Words used on this page" lede={<p>Short, plain definitions of the terms above.</p>}>
        <dl className="grid gap-x-10 gap-y-6 sm:grid-cols-2 lg:grid-cols-3">
          {GLOSSARY.map((g) => (
            <div key={g.term} className="border-t border-(--line) pt-4">
              <dt className="text-[15px] font-medium">{g.term}</dt>
              <dd className="mt-1.5 text-[14px] leading-[1.6] text-(--muted)">{g.plain}</dd>
            </div>
          ))}
        </dl>
      </Section>

      {/* ------------------------------------------------------------------ for engineers */}
      <Section
        id="details"
        title="For engineers: every measurement"
        lede={<p>The raw stage table, the accuracy-against-speed plot, and the notes the toolkit printed during the run.</p>}
      >
        <Disclosure label="Show the full measurements">
          <div className="grid gap-10 lg:grid-cols-[1.2fr_1fr] lg:items-center">
            <div className="overflow-x-auto">
              <table className="figures-tab w-full min-w-[560px] text-left text-[13px]">
                <thead className="text-[11px] uppercase tracking-[0.06em] text-(--muted)">
                  <tr>
                    <th className="pb-2 font-medium">Stage</th>
                    <th className="pb-2 font-medium">Precision</th>
                    <th className="pb-2 text-right font-medium">Top-1</th>
                    <th className="pb-2 text-right font-medium">Median</th>
                    <th className="pb-2 text-right font-medium">p95</th>
                    <th className="pb-2 text-right font-medium">Size</th>
                    <th className="pb-2 text-right font-medium">Params</th>
                  </tr>
                </thead>
                <tbody>
                  {[b, ...m.stages].map((s) => (
                    <tr key={s.stage} className="border-t border-(--line)">
                      <td className="py-2 font-mono text-[12px]">{s.stage}</td>
                      <td className="py-2">{s.precision}</td>
                      <td className="py-2 text-right">{pct(s.accuracy)}</td>
                      <td className="py-2 text-right">{ms(s.median_ms)}</td>
                      <td className="py-2 text-right">{ms(s.p95_ms)}</td>
                      <td className="py-2 text-right">{mb(s.size_mb)}</td>
                      <td className="py-2 text-right">{count(s.parameters)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {ps && ps.macs_before != null && ps.macs_after != null ? (
                <p className="mt-4 text-[13px] text-(--muted)">
                  Multiply-accumulates per image: {(ps.macs_before / 1e6).toFixed(1)}M to {(ps.macs_after / 1e6).toFixed(1)}M.
                </p>
              ) : null}
            </div>
            <ParetoMini stages={[b, ...m.stages]} className="w-full" />
          </div>
          <p className="mt-6 text-[13px] text-(--muted)">Settings: {m.schedule}.</p>
          {m.warnings.length > 0 ? (
            <ul className="mt-6 space-y-2 text-[13px] text-(--muted)">
              {m.warnings.map((w) => (
                <li key={w} className="break-words border-l-2 border-(--line-strong) pl-4">
                  {w}
                </li>
              ))}
            </ul>
          ) : null}
          <Provenance p={m.provenance} source={m.source} />
        </Disclosure>
      </Section>
    </>
  );
}

export default function ModelPage({ params }: { params: Promise<{ slug: string }> }) {
  return (
    <PageFrame>
      <Suspense fallback={<div className="min-h-[70svh]" aria-busy="true" />}>
        <ModelBody params={params} />
      </Suspense>
    </PageFrame>
  );
}
