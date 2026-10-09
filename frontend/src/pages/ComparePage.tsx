import { useQuery } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { FilterBar } from '../components/filters/FilterBar'
import { StatusPill } from '../components/ui/StatusPill'
import { useAnalysisQuery } from '../hooks/useAnalysisQuery'
import { API_BASE, ApiRequestError, getComparison, getRegions, getTimeSeries } from '../lib/api'

export function ComparePage() {
  const filters = useAnalysisQuery()
  const regions = useQuery({ queryKey: ['regions'], queryFn: getRegions })
  const states = regions.data?.regions.filter((region) => region.level === 'ADM1') ?? []
  const [selected, setSelected] = useState<string[]>([])
  const compareQuery = useMemo(() => {
    const params = new URLSearchParams(filters.queryString)
    params.delete('region_id')
    selected.forEach((id) => params.append('region_id', id))
    return params.toString()
  }, [filters.queryString, selected])
  const comparison = useQuery({
    queryKey: ['compare', compareQuery],
    queryFn: () => getComparison(compareQuery),
    enabled: selected.length >= 2,
  })
  const series = useQuery({
    queryKey: ['compare-series', compareQuery],
    enabled: selected.length >= 2 && comparison.isSuccess,
    queryFn: async () => {
      const responses = await Promise.all(
        selected.map((id) => {
          const params = new URLSearchParams(filters.queryString)
          params.set('region_id', id)
          return getTimeSeries(params.toString())
        }),
      )
      return responses
    },
  })

  function toggle(id: string) {
    setSelected((current) => (current.includes(id) ? current.filter((item) => item !== id) : [...current, id]))
  }

  const chartRows = mergeSeries(series.data ?? [])

  return (
    <section className="space-y-6">
      <div>
        <h2 className="text-3xl font-semibold text-white">Region comparison</h2>
        <p className="mt-2 text-muted">
          State and region trends are adjusted together with Benjamini–Hochberg. Choose at least two.
        </p>
      </div>
      <FilterBar />
      <div className="flex flex-wrap gap-2">
        {states.map((region) => (
          <label key={region.id} className="rounded-full border border-line px-3 py-1 text-sm">
            <input
              className="mr-2"
              type="checkbox"
              checked={selected.includes(region.id)}
              onChange={() => toggle(region.id)}
            />
            {region.name}
          </label>
        ))}
      </div>
      {comparison.error ? (
        <p className="text-heat">
          {comparison.error instanceof ApiRequestError ? comparison.error.message : comparison.error.message}
        </p>
      ) : null}
      {comparison.data ? (
        <div className="overflow-x-auto rounded-2xl border border-line">
          <table className="w-full text-left text-sm">
            <thead className="bg-panel text-muted">
              <tr>
                <th className="px-4 py-3">Region</th>
                <th className="px-4 py-3">Slope</th>
                <th className="px-4 py-3">Adjusted p</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Coverage</th>
              </tr>
            </thead>
            <tbody>
              {comparison.data.regions.map((region) => (
                <tr key={region.geography_id} className="border-t border-line">
                  <td className="px-4 py-3">{region.geography_name}</td>
                  <td className="px-4 py-3">
                    {region.slope_text} {region.slope_unit}
                  </td>
                  <td className="px-4 py-3">{region.adjusted_p_value?.toFixed(4) ?? 'n/a'}</td>
                  <td className="px-4 py-3">
                    <StatusPill status={region.trend_status} />
                  </td>
                  <td className="px-4 py-3">
                    {region.coverage_fraction == null ? 'n/a' : `${Math.round(region.coverage_fraction * 100)}%`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
      {chartRows.length ? (
        <div className="h-80 rounded-2xl border border-line bg-panel p-4">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartRows}>
              <CartesianGrid stroke="#314038" vertical={false} />
              <XAxis dataKey="year" stroke="#93a79b" />
              <YAxis stroke="#93a79b" width={56} />
              <Tooltip contentStyle={{ background: '#18211c', border: '1px solid #314038' }} />
              {(series.data ?? []).map((item, index) => (
                <Line
                  key={item.region_id}
                  type="monotone"
                  dataKey={item.region_name}
                  stroke={palette[index % palette.length]}
                  dot={false}
                  connectNulls={false}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : null}
      {selected.length >= 2 ? (
        <a className="inline-block text-sm text-accent" href={`${API_BASE}/export/trends.csv?${filters.queryString}`}>
          Download grid trend CSV for the current variable
        </a>
      ) : null}
    </section>
  )
}

const palette = ['#e0a15a', '#79b4d6', '#7dbe8a', '#e07a5f', '#d7e2da', '#c084fc']

function mergeSeries(series: Array<{ region_name: string; data: Array<{ year: number; value: number | null }> }>) {
  const byYear = new Map<number, Record<string, number | string | null>>()
  for (const item of series) {
    for (const point of item.data) {
      const row = byYear.get(point.year) ?? { year: point.year }
      row[item.region_name] = point.value
      byYear.set(point.year, row)
    }
  }
  return [...byYear.values()].sort((a, b) => Number(a.year) - Number(b.year))
}
