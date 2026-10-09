import { useQuery } from '@tanstack/react-query'
import { FilterBar } from '../components/filters/FilterBar'
import { TrendMap } from '../components/maps/TrendMap'
import { statusColor } from '../components/ui/StatusPill'
import { useAnalysisQuery } from '../hooks/useAnalysisQuery'
import { API_BASE, ApiRequestError, getGrid } from '../lib/api'

const legend = [
  ['significant_increasing', 'Significant increase'],
  ['significant_decreasing', 'Significant decrease'],
  ['not_significant', 'Not significant'],
  ['insufficient_data', 'Insufficient data'],
] as const

export function MapExplorerPage() {
  const filters = useAnalysisQuery()
  const grid = useQuery({
    queryKey: ['grid', filters.queryString],
    queryFn: () => getGrid(filters.queryString),
  })

  return (
    <section className="space-y-6">
      <div>
        <h2 className="text-3xl font-semibold text-white">Map explorer</h2>
        <p className="mt-2 max-w-3xl text-muted">
          Each cell is kept only when its centre falls inside the Myanmar boundary. Colours follow
          the Benjamini–Hochberg adjusted status, not the raw slope alone.
        </p>
      </div>
      <FilterBar />
      <ul className="flex flex-wrap gap-3 text-sm">
        {legend.map(([status, label]) => (
          <li key={status} className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-sm" style={{ background: statusColor[status] }} />
            {label}
          </li>
        ))}
      </ul>
      {grid.isLoading ? <p>Calculating grid trends…</p> : null}
      {grid.error ? (
        <p className="text-heat">{grid.error instanceof ApiRequestError ? grid.error.message : grid.error.message}</p>
      ) : null}
      {grid.data ? (
        <>
          <TrendMap features={grid.data.features} mapKey={filters.queryString} />
          <a className="inline-block text-sm text-accent" href={`${API_BASE}/export/trends.geojson?${filters.queryString}`}>
            Download GeoJSON
          </a>
        </>
      ) : null}
    </section>
  )
}
