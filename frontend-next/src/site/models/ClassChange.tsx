import { pct } from '@/src/data/results';

export type ClassRow = { name: string; before: number; after: number };

/**
 * Per-category accuracy, original against compressed, worst change first.
 * Both bars share one 0-100% scale so the gap between them is the change.
 */
export function ClassChange({ rows }: { rows: ClassRow[] }) {
  return (
    <div>
      <div className="mb-5 flex flex-wrap gap-5 text-[13px] text-(--muted)">
        <span className="inline-flex items-center gap-2">
          <span className="h-2 w-5 rounded-full bg-(--snake)" aria-hidden="true" /> Original model
        </span>
        <span className="inline-flex items-center gap-2">
          <span className="h-2 w-5 rounded-full bg-int8" aria-hidden="true" /> Compressed model
        </span>
      </div>
      <ul className="figures-tab space-y-4">
        {rows.map((r) => {
          const change = (r.after - r.before) * 100;
          return (
            <li key={r.name} className="grid grid-cols-[92px_minmax(0,1fr)_88px] items-center gap-4 sm:grid-cols-[120px_minmax(0,1fr)_120px]">
              <span className="text-[15px] capitalize">{r.name}</span>
              <div className="space-y-1.5" aria-label={`${r.name}: ${pct(r.before, 1)} before, ${pct(r.after, 1)} after`}>
                <div className="flex items-center gap-3">
                  <div className="h-2 flex-1 overflow-hidden rounded-full bg-(--line)">
                    <div className="h-full rounded-full bg-(--snake)" style={{ width: `${r.before * 100}%` }} />
                  </div>
                  <span className="w-12 text-right text-[12px] text-(--muted)">{pct(r.before, 1)}</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="h-2 flex-1 overflow-hidden rounded-full bg-(--line)">
                    <div className="h-full rounded-full bg-int8" style={{ width: `${r.after * 100}%` }} />
                  </div>
                  <span className="w-12 text-right text-[12px] text-(--muted)">{pct(r.after, 1)}</span>
                </div>
              </div>
              <span className="text-right text-[14px]">
                {change > 0 ? '+' : ''}
                {change.toFixed(1)} <span className="text-[12px] text-(--muted)">points</span>
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
