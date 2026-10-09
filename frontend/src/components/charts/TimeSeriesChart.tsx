import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { SeriesPoint } from '../../types/api'

export function TimeSeriesChart({
  points,
  trendLine,
  unit,
}: {
  points: SeriesPoint[]
  trendLine: Array<{ year: number; value: number }>
  unit: string
}) {
  const trendByYear = new Map(trendLine.map((point) => [point.year, point.value]))
  const rows = points.map((point) => ({
    label: point.month ? `${point.year}-${String(point.month).padStart(2, '0')}` : String(point.year),
    value: point.value,
    trend: point.month ? null : (trendByYear.get(point.year) ?? null),
  }))

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={rows} margin={{ top: 10, right: 12, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="#314038" vertical={false} />
          <XAxis dataKey="label" stroke="#93a79b" minTickGap={24} />
          <YAxis stroke="#93a79b" width={56} />
          <Tooltip
            contentStyle={{ background: '#18211c', border: '1px solid #314038' }}
            formatter={(value, name) => [
              value == null ? 'Missing' : `${value} ${unit}`,
              name === 'trend' ? 'Sen line' : 'Value',
            ]}
          />
          <Line type="monotone" dataKey="value" stroke="#e0a15a" strokeWidth={2} dot={false} connectNulls={false} />
          <Line type="monotone" dataKey="trend" stroke="#d7e2da" strokeDasharray="4 4" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
