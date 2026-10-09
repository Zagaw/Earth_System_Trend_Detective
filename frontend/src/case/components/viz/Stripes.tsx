import { domainMax, paint } from '../../lib/colors'
import { formatSigned, isFiniteNumber, unitShort } from '../../lib/format'
import type { SeriesPoint, VariableId } from '../../types'

export function Stripes({
  series,
  variable,
  reference,
}: {
  series: SeriesPoint[]
  variable: VariableId
  reference: string
}) {
  const span = domainMax(series.map((point) => point.anomaly))
  const first = series[0]?.year
  const last = series.at(-1)?.year
  return (
    <div>
      <div className="flex h-20 overflow-hidden rounded-xl border border-line">
        {series.map((point) => (
          <div
            key={point.year}
            className="h-full flex-1"
            style={{ background: paint(variable, point.anomaly, span) }}
            title={
              isFiniteNumber(point.anomaly)
                ? `${point.year}: ${formatSigned(point.anomaly, 2)} ${unitShort(variable)} vs ${reference}`
                : `${point.year}: no value`
            }
          />
        ))}
      </div>
      <div className="mt-1 flex justify-between text-xs text-muted">
        <span>{first}</span>
        <span>{last}</span>
      </div>
    </div>
  )
}
