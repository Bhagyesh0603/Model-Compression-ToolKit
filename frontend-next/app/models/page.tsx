import type { Metadata } from 'next';
import Link from 'next/link';
import { ArrowUpRight, CircleCheck, FileArchive, NotebookPen, Timer } from 'lucide-react';
import { finalStage, mb, models, ms, pct, ratio, runCount, slugOf, untested } from '@/src/data/results';
import { PageFrame } from '@/src/site/PageFrame';
import { Wrap } from '@/src/site/Section';
import { MODEL_INTRO } from '@/src/site/modelGuide';
import { AnimBar } from '@/src/viz/AnimBar';
import { Reveal } from '@/src/landing/Motion';

export const metadata: Metadata = { title: 'Compressed models — compresskit' };

const READING_KEY = [
  {
    icon: CircleCheck,
    title: 'Correct answers',
    text: 'Out of the test photos, how many the model labels correctly. We want this to stay close to the original.',
  },
  {
    icon: FileArchive,
    title: 'File size',
    text: 'How much space the model takes. Smaller is cheaper to store, quicker to download, and fits on small devices.',
  },
  {
    icon: Timer,
    title: 'Time per photo',
    text: 'How long the model takes to answer for one photo, timed on a real computer. Shorter is faster.',
  },
];

export default function ModelsPage() {
  return (
    <PageFrame>
      <Wrap className="pb-12 pt-16 sm:pt-24">
        <Reveal>
          <p className="label-xs">Compressed models</p>
          <h1 className="mt-4 max-w-[20ch] text-balance text-[clamp(38px,5vw,70px)] font-normal leading-[1.03] tracking-[-0.045em]">
            Smaller, faster models that still see clearly
          </h1>
          <div className="mt-8 grid gap-8 lg:grid-cols-[1.3fr_1fr] lg:gap-16">
            <div className="space-y-4 text-[18px] leading-[1.65]">
              <p>
                An image-recognition model is a program that looks at a photo and says what is in it. It is stored as a file of
                learned numbers, often far more of them than the task really needs.
              </p>
              <p className="text-(--muted)">
                compresskit takes a trained model and shrinks it: it removes the parts that barely help, lets the model practise to
                recover, and stores its numbers more compactly. Then it measures what that cost. Each card below is one model we
                put through that process.
              </p>
            </div>
            <dl className="grid grid-cols-3 gap-4 self-end rounded-[24px] border border-(--line) p-6 text-center">
              <div>
                <dt className="text-[12px] text-(--muted)">Models tested</dt>
                <dd className="mt-1 text-[40px] leading-none tracking-[-0.04em]">{models.length}</dd>
              </div>
              <div>
                <dt className="text-[12px] text-(--muted)">Test runs</dt>
                <dd className="mt-1 text-[40px] leading-none tracking-[-0.04em]">{runCount}</dd>
              </div>
              <div>
                <dt className="text-[12px] text-(--muted)">Ready to run</dt>
                <dd className="mt-1 text-[40px] leading-none tracking-[-0.04em]">{untested.length}</dd>
              </div>
            </dl>
          </div>
        </Reveal>
      </Wrap>

      <Wrap className="pb-12">
        <div className="rounded-[24px] bg-(--surface) p-6 sm:p-8">
          <h2 className="text-[13px] uppercase tracking-[0.08em] text-(--muted)">How to read each card</h2>
          <ul className="mt-5 grid gap-6 md:grid-cols-3">
            {READING_KEY.map(({ icon: Icon, title, text }) => (
              <li key={title} className="flex gap-4">
                <Icon className="mt-0.5 h-5 w-5 shrink-0 text-(--snake)" aria-hidden="true" />
                <div>
                  <p className="text-[16px] font-medium">{title}</p>
                  <p className="mt-1 text-[14px] leading-[1.6] text-(--muted)">{text}</p>
                </div>
              </li>
            ))}
          </ul>
          <p className="mt-6 flex flex-wrap items-center gap-x-5 gap-y-2 text-[13px] text-(--muted)">
            <span className="inline-flex items-center gap-2">
              <span className="h-2 w-5 rounded-full bg-(--snake)" aria-hidden="true" /> Original model
            </span>
            <span className="inline-flex items-center gap-2">
              <span className="h-2 w-5 rounded-full bg-int8" aria-hidden="true" /> Compressed model
            </span>
          </p>
        </div>
      </Wrap>

      <Wrap className="pb-20">
        <ul className="grid gap-4 lg:grid-cols-3">
          {models.map((m) => {
            const b = m.baseline;
            const f = finalStage(m);
            const intro = MODEL_INTRO[m.arch];
            const headline = m.runs.find((r) => r.primary);
            return (
              <li key={m.arch} className="h-full">
                <Link
                  href={`/models/${slugOf(m.arch)}`}
                  className="group flex h-full flex-col rounded-[24px] border border-(--line) p-6 transition-colors hover:bg-(--hover) sm:p-7"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-[12px] text-(--muted)">{intro?.family ?? m.dataset}</p>
                      <h2 className="mt-1 text-[30px] tracking-[-0.03em]">{m.name}</h2>
                    </div>
                    <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-(--chip) transition-all duration-300 group-hover:rotate-45 group-hover:bg-brand-600 group-hover:text-white">
                      <ArrowUpRight className="h-4 w-4" aria-hidden="true" />
                    </span>
                  </div>

                  <p className="mt-4 text-[17px] leading-snug">
                    <strong className="font-medium">{ratio(m.totals.size_reduction)} smaller</strong>, {ratio(m.totals.speedup)} faster,{' '}
                    {m.totals.accuracy_drop_pp.toFixed(2)} points less accurate.
                  </p>

                  <div className="mt-6 space-y-5">
                    <div className="space-y-2">
                      <AnimBar label="Correct answers, before" value={b.accuracy} display={pct(b.accuracy)} />
                      <AnimBar label="Correct answers, after" value={f.accuracy} display={pct(f.accuracy)} accent />
                    </div>
                    <div className="space-y-2">
                      <AnimBar label="File size, before" value={1} display={mb(b.size_mb)} />
                      <AnimBar label="File size, after" value={f.size_mb / b.size_mb} display={mb(f.size_mb)} accent />
                    </div>
                    <div className="space-y-2">
                      <AnimBar label="Time per photo, before" value={1} display={ms(b.median_ms)} />
                      <AnimBar label="Time per photo, after" value={f.median_ms / b.median_ms} display={ms(f.median_ms)} accent />
                    </div>
                  </div>

                  <p className="mt-auto pt-6 text-[13px] leading-[1.6] text-(--muted)">
                    Tested {m.runs.length === 1 ? 'once' : `${m.runs.length} times`}. Shown: the {headline?.machine ?? m.provenance.host} run
                    {m.provenance.kind === 'transcribed' ? ', typed in from its log' : ''}.
                    {m.host.int8_speed === 'slow' ? ' That computer lacks fast 8-bit maths, so the speed gain is understated.' : ''}
                  </p>
                  <span className="mt-4 text-[14px] underline decoration-(--line-strong) underline-offset-4 group-hover:decoration-current">
                    See how it was done
                  </span>
                </Link>
              </li>
            );
          })}
        </ul>
      </Wrap>

      {untested.length > 0 ? (
        <Wrap className="pb-24">
          <div className="rounded-[24px] border border-dashed border-(--line-strong) p-6 sm:p-8">
            <div className="flex items-start gap-4">
              <NotebookPen className="mt-1 h-5 w-5 shrink-0 text-(--muted)" aria-hidden="true" />
              <div>
                <h2 className="text-[22px] tracking-[-0.02em]">Not tested yet</h2>
                <p className="mt-2 max-w-[70ch] text-[15px] leading-[1.65] text-(--muted)">
                  These models have a ready-made notebook in the repository but no recorded run yet, so there are no results to
                  show. They will appear above once a run is recorded.
                </p>
                <ul className="mt-5 flex flex-wrap gap-2">
                  {untested.map((u) => (
                    <li key={u.notebook} className="rounded-full bg-(--chip) px-3 py-1.5 text-[13px] text-(--chip-fg)" title={u.notebook}>
                      {u.name} <span className="opacity-70">· {u.dataset}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </Wrap>
      ) : null}
    </PageFrame>
  );
}
