import { domainMax, paint } from '../../lib/colors'
import { formatSigned, isFiniteNumber } from '../../lib/format'
import type { SeriesPoint } from '../../types'

export function RainBars({ series, reference }: { series: SeriesPoint[]; reference: string }) {
  const finite = series.map((point) => point.value).filter(isFiniteNumber)
  const maxValue = finite.length ? Math.max(...finite) : 1
  const span = domainMax(series.map((point) => point.anomaly))
  return (
    <div className="flex h-24 items-end gap-0.5" aria-label="Yearly rainfall colored by anomaly">
      {series.map((point) => (
        <div
          key={point.year}
          className="flex-1 rounded-sm"
          style={{
            height: isFiniteNumber(point.value) ? `${Math.max(8, (point.value / maxValue) * 100)}%` : '6%',
            background: isFiniteNumber(point.anomaly) ? paint('precipitation', point.anomaly, span) : '#334155',
          }}
          title={
            isFiniteNumber(point.value)
              ? `${point.year}: ${point.value.toFixed(0)} mm${
                  isFiniteNumber(point.anomaly) ? `, ${formatSigned(point.anomaly, 0)} mm vs ${reference}` : ''
                }`
              : `${point.year}: no value`
          }
        />
      ))}
    </div>
  )
}
