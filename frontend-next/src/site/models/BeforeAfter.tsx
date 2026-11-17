import type { ReactNode } from 'react';
import { AnimBar } from '@/src/viz/AnimBar';

/**
 * One question a non-specialist would ask ("is it still accurate?"), answered with the recorded
 * before and after values as two bars on the same scale, and a one-line verdict.
 */
export function BeforeAfter({
  question,
  term,
  before,
  after,
  beforeShown,
  afterShown,
  verdict,
  explain,
  scaleMax,
}: {
  question: string;
  /** The technical name, shown small, so readers can match it to the glossary. */
  term: string;
  before: number;
  after: number;
  beforeShown: string;
  afterShown: string;
  verdict: ReactNode;
  explain: ReactNode;
  /** Bar scale; defaults to the larger of the two values. */
  scaleMax?: number;
}) {
  const max = scaleMax ?? Math.max(before, after);
  return (
    <div className="flex h-full flex-col rounded-[24px] border border-(--line) p-6 sm:p-7">
      <p className="text-[12px] uppercase tracking-[0.08em] text-(--muted)">{term}</p>
      <h3 className="mt-2 text-[20px] leading-tight tracking-[-0.02em]">{question}</h3>
      <p className="mt-5 text-[clamp(28px,2.6vw,38px)] leading-none tracking-[-0.04em]">{verdict}</p>
      <div className="mt-6 space-y-3">
        <AnimBar label="Original model" value={before / max} display={beforeShown} />
        <AnimBar label="Compressed model" value={after / max} display={afterShown} accent delay={0.15} />
      </div>
      <p className="mt-auto pt-6 text-[14px] leading-[1.6] text-(--muted)">{explain}</p>
    </div>
  );
}
