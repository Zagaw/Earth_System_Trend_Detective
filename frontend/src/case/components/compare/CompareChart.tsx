import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { isFiniteNumber, unitShort } from '../../lib/format'
import type { PlaceRecord, VariableId } from '../../types'

export function CompareChart({
  variable,
  left,
  right,
}: {
  variable: VariableId
  left: PlaceRecord
  right: PlaceRecord
}) {
  const rightValue = new Map(right.series.map((point) => [point.year, point.value]))
  const leftTrend = new Map(left.trend_line.map((point) => [point.year, point.value]))
  const rightTrend = new Map(right.trend_line.map((point) => [point.year, point.value]))
  const rows = left.series.map((point) => ({
    year: point.year,
    a: point.value,
    b: rightValue.get(point.year) ?? null,
    aTrend: leftTrend.get(point.year) ?? null,
    bTrend: rightTrend.get(point.year) ?? null,
  }))
  const unit = unitShort(variable)
  return (
    <div className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={rows} margin={{ top: 12, right: 8, left: 0, bottom: 0 }}>
          <XAxis dataKey="year" tick={{ fill: '#94A3B8', fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: '#94A3B8', fontSize: 11 }} axisLine={false} tickLine={false} width={48} />
          <Tooltip
            contentStyle={{ background: '#0F1733', border: '1px solid #1F2A52', borderRadius: 12 }}
            formatter={(value, name) => [
              isFiniteNumber(Number(value)) ? `${Number(value).toFixed(2)} ${unit}` : 'no value',
              String(name),
            ]}
          />
          <Line name={left.geography_name} dataKey="a" stroke="#FB923C" strokeWidth={2} dot={false} connectNulls={false} />
          <Line name={right.geography_name} dataKey="b" stroke="#2DD4BF" strokeWidth={2} dot={false} connectNulls={false} />
          <Line name={`${left.geography_name} trend`} dataKey="aTrend" stroke="#FB923C" strokeDasharray="4 4" dot={false} />
          <Line name={`${right.geography_name} trend`} dataKey="bTrend" stroke="#2DD4BF" strokeDasharray="4 4" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
