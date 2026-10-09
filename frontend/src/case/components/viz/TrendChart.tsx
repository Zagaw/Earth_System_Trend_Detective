import { Line, LineChart, ReferenceArea, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { isFiniteNumber, unitShort } from '../../lib/format'
import type { PlaceRecord, VariableId } from '../../types'

export function TrendChart({
  place,
  variable,
  baselineStart,
  baselineEnd,
  comparisonStart,
  comparisonEnd,
}: {
  place: PlaceRecord
  variable: VariableId
  baselineStart: number
  baselineEnd: number
  comparisonStart: number
  comparisonEnd: number
}) {
  const trend = new Map(place.trend_line.map((point) => [point.year, point.value]))
  const rows = place.series.map((point) => ({
    year: point.year,
    value: point.value,
    trend: trend.get(point.year) ?? null,
  }))
  const unit = unitShort(variable)
  return (
    <div className="h-56">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={rows} margin={{ top: 16, right: 8, left: 0, bottom: 0 }}>
          <XAxis dataKey="year" tick={{ fill: '#94A3B8', fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis
            tick={{ fill: '#94A3B8', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={48}
            domain={['auto', 'auto']}
          />
          <Tooltip
            contentStyle={{ background: '#0F1733', border: '1px solid #1F2A52', borderRadius: 12 }}
            labelStyle={{ color: '#F8FAFC' }}
            formatter={(value, name) => {
              const label = name === 'trend' ? "Sen's line" : 'Value'
              return [isFiniteNumber(Number(value)) ? `${Number(value).toFixed(2)} ${unit}` : 'no value', label]
            }}
          />
          <ReferenceArea x1={baselineStart} x2={baselineEnd} fill="#FBBF24" fillOpacity={0.08} />
          <ReferenceArea x1={comparisonStart} x2={comparisonEnd} fill="#38BDF8" fillOpacity={0.08} />
          <Line dataKey="value" stroke="#F8FAFC" strokeWidth={2} dot={{ r: 2 }} connectNulls={false} />
          <Line dataKey="trend" stroke="#FBBF24" strokeDasharray="5 4" dot={false} connectNulls />
        </LineChart>
      </ResponsiveContainer>
      <p className="text-xs text-muted">
        Gold band {baselineStart}–{baselineEnd}. Blue band {comparisonStart}–{comparisonEnd}. Dashed line is Sen's slope.
      </p>
    </div>
  )
}
