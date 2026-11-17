/**
 * "Out of every 100 photos": a 10 x 10 grid where filled dots are right answers and hollow dots are mistakes.
 * Rounded to the nearest whole photo, so the caption says "about".
 */
export function DotGrid({ correct, label, accent = false }: { correct: number; label: string; accent?: boolean }) {
  const n = Math.max(0, Math.min(100, correct));
  return (
    <figure className="m-0">
      <div
        role="img"
        aria-label={`${label}: about ${n} of every 100 test photos labelled correctly`}
        className="grid w-full max-w-[220px] grid-cols-10 gap-[5px]"
      >
        {Array.from({ length: 100 }, (_, i) => (
          <span
            key={i}
            className={`aspect-square rounded-full ${
              i < n ? (accent ? 'bg-int8' : 'bg-(--snake)') : 'border border-(--line-strong) bg-transparent'
            }`}
          />
        ))}
      </div>
      <figcaption className="mt-3 text-[13px] leading-snug">
        <span className="font-medium">{label}</span>
        <span className="block text-(--muted)">
          about {n} right, {100 - n} wrong
        </span>
      </figcaption>
    </figure>
  );
}
