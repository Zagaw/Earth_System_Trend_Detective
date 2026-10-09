import { isFiniteNumber } from '../../lib/format'

export function PValueGauge({ pValue, alpha }: { pValue: number | null; alpha: number }) {
  if (!isFiniteNumber(pValue)) {
    return <p className="text-sm text-muted">Corrected p-value is unavailable for this series.</p>
  }
  const marker = Math.min(Math.max(pValue, 0), 1) * 100
  return (
    <div>
      <p className="tabular text-sm text-ink">{pValue < 0.001 ? '< 0.001' : pValue.toFixed(4)}</p>
      <div className="relative mt-2 h-2 rounded-full bg-[#1E293B]">
        <div className="absolute top-[-3px] h-3.5 w-px bg-gold" style={{ left: `${alpha * 100}%` }} />
        <div
          className="absolute top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-navy bg-ink"
          style={{ left: `${marker}%` }}
        />
      </div>
      <p className="mt-2 text-xs text-muted">
        The mark is the corrected p-value. The gold line is {alpha}. This gauge does not rerun the test.
      </p>
    </div>
  )
}
