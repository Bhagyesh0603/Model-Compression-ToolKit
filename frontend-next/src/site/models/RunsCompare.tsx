import { count, mb, ms, pct, ratio, type RunSummary } from '@/src/data/results';

const isShortTest = (r: RunSummary) => r.schedule.includes('short smoke run');

function Chip({ children, strong = false }: { children: React.ReactNode; strong?: boolean }) {
  return (
    <span
      className={`inline-flex h-6 items-center rounded-full px-2.5 text-[11px] font-medium ${
        strong ? 'bg-(--inv-bg) text-(--inv-fg)' : 'bg-(--chip) text-(--chip-fg)'
      }`}
    >
      {children}
    </span>
  );
}

function Metric({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div>
      <dt className="text-[12px] text-(--muted)">{label}</dt>
      <dd className="mt-1 text-[22px] leading-none tracking-[-0.03em]">{value}</dd>
      <dd className="mt-1.5 text-[12px] leading-snug text-(--muted)">{sub}</dd>
    </div>
  );
}

/** Every recorded run of one model, side by side, with a plain explanation of why they differ. */
export function RunsCompare({ runs }: { runs: RunSummary[] }) {
  const real = runs.filter((r) => !isShortTest(r));
  const mostAccurate = real.length > 1 ? real.reduce((a, b) => (b.final.accuracy > a.final.accuracy ? b : a)) : null;
  const smallest = real.length > 1 ? real.reduce((a, b) => (b.totals.size_reduction > a.totals.size_reduction ? b : a)) : null;
  const fast = [...new Set(runs.filter((r) => r.int8_speed === 'fast').map((r) => r.machine.replace(/ \(short test\)$/, '')))];
  const slow = [...new Set(runs.filter((r) => r.int8_speed === 'slow').map((r) => r.machine))];

  return (
    <div className="space-y-10">
      <ol className="grid gap-4 lg:grid-cols-2">
        {runs.map((r, i) => {
          const drop = (r.baseline.accuracy - r.final.accuracy) * 100;
          return (
            <li key={r.id} className={`flex flex-col rounded-[24px] border p-6 ${r.primary ? 'border-(--line-strong)' : 'border-(--line)'}`}>
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-[12px] text-(--muted)">Run {i + 1}</span>
                {r.primary ? <Chip strong>Shown on this page</Chip> : null}
                {isShortTest(r) ? <Chip>Short test, not a result</Chip> : null}
                {mostAccurate && r.id === mostAccurate.id ? <Chip>Most accurate</Chip> : null}
                {smallest && r.id === smallest.id ? <Chip>Smallest file</Chip> : null}
                {r.kind === 'transcribed' ? <Chip>Typed in from a log</Chip> : null}
              </div>
              <h3 className="mt-3 text-[22px] tracking-[-0.02em]">{r.machine}</h3>
              <p className="mt-1 text-[13px] text-(--muted)">
                {r.cpu}
                {r.date ? ` · ${r.date}` : ''}
              </p>
              <dl className="figures-tab mt-6 grid grid-cols-3 gap-4">
                <Metric
                  label="Correct answers"
                  value={pct(r.final.accuracy)}
                  sub={`from ${pct(r.baseline.accuracy)}, ${drop.toFixed(2)} points lower`}
                />
                <Metric label="File size" value={`${ratio(r.totals.size_reduction)} smaller`} sub={`${mb(r.baseline.size_mb)} to ${mb(r.final.size_mb)}`} />
                <Metric
                  label="Speed"
                  value={`${ratio(r.totals.speedup)} faster`}
                  sub={`${ms(r.baseline.median_ms)} to ${ms(r.final.median_ms)}${r.int8_speed === 'slow' ? ', no fast INT8 here' : ''}`}
                />
              </dl>
              <p className="mt-6 border-t border-(--line) pt-4 text-[13px] leading-[1.6] text-(--muted)">
                <span className="text-(--fg)">Parameters kept:</span> {count(r.params_before)} became {count(r.params_after)}
                {r.steps ? `, cut in ${r.steps} step${r.steps === 1 ? '' : 's'}` : ''}.
                <span className="mt-1 block">
                  <span className="text-(--fg)">Settings:</span> {r.schedule}.
                </span>
              </p>
            </li>
          );
        })}
      </ol>

      {runs.length > 1 ? (
        <div className="grid gap-6 rounded-[24px] bg-(--surface) p-6 sm:p-8 lg:grid-cols-3">
          <div>
            <h3 className="text-[17px] font-medium">Different settings</h3>
            <p className="mt-2 text-[14px] leading-[1.65] text-(--muted)">
              Each run chose how much to cut and how long to practise afterwards. Cutting more makes the file smaller but costs
              more accuracy.
              {mostAccurate && smallest && mostAccurate.id !== smallest.id
                ? ` Here the ${mostAccurate.machine} run kept the most accuracy, while the ${smallest.machine} run cut deeper and produced the smallest file.`
                : ''}
            </p>
          </div>
          <div>
            <h3 className="text-[17px] font-medium">Different computers</h3>
            <p className="mt-2 text-[14px] leading-[1.65] text-(--muted)">
              Speed is timed on the computer that ran the test, so it changes from machine to machine.
              {fast.length ? ` ${fast.join(' and ')} ${fast.length > 1 ? 'have' : 'has'} fast 8-bit maths, so the speed-up there is real.` : ''}
              {slow.length ? ` ${slow.join(' and ')} ${slow.length > 1 ? 'do' : 'does'} not, so its speed figure understates what the compressed model can do.` : ''}
            </p>
          </div>
          <div>
            <h3 className="text-[17px] font-medium">What stays the same</h3>
            <p className="mt-2 text-[14px] leading-[1.65] text-(--muted)">
              Accuracy and file size do not depend on which computer measured them. They depend on the settings, and a little on
              chance during training.
              {runs.some(isShortTest) ? ' The short test run only checks that the pipeline works end to end; it is listed for completeness.' : ''}
            </p>
          </div>
        </div>
      ) : null}
    </div>
  );
}
