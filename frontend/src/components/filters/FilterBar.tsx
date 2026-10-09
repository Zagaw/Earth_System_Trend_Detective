import { useQuery } from '@tanstack/react-query'
import { getRegions } from '../../lib/api'
import { useAnalysisQuery, variables } from '../../hooks/useAnalysisQuery'

const seasons = [
  ['DJF', 'DJF (Dec–Feb)'],
  ['MAM', 'MAM (Mar–May)'],
  ['JJA', 'JJA (Jun–Aug)'],
  ['SON', 'SON (Sep–Nov)'],
  ['monsoon', 'Monsoon (May–Oct)'],
] as const

export function FilterBar() {
  const filters = useAnalysisQuery()
  const regions = useQuery({ queryKey: ['regions'], queryFn: getRegions })

  return (
    <form className="grid gap-3 rounded-2xl border border-line bg-panel p-4 md:grid-cols-3 xl:grid-cols-6">
      <label className="text-sm">
        <span className="mb-1 block text-muted">Variable</span>
        <select
          className="w-full rounded-lg border border-line bg-ink px-3 py-2"
          value={filters.variable}
          onChange={(event) => filters.update('variable', event.target.value)}
        >
          {variables.map((variable) => (
            <option key={variable} value={variable}>
              {variable === 'relative_humidity' ? 'Relative humidity' : variable}
            </option>
          ))}
        </select>
      </label>
      <label className="text-sm">
        <span className="mb-1 block text-muted">Start year</span>
        <input
          className="w-full rounded-lg border border-line bg-ink px-3 py-2"
          type="number"
          min={1981}
          max={2100}
          value={filters.startYear}
          onChange={(event) => filters.update('start', event.target.value)}
        />
      </label>
      <label className="text-sm">
        <span className="mb-1 block text-muted">End year</span>
        <input
          className="w-full rounded-lg border border-line bg-ink px-3 py-2"
          type="number"
          min={1981}
          max={2100}
          value={filters.endYear}
          onChange={(event) => filters.update('end', event.target.value)}
        />
      </label>
      <label className="text-sm">
        <span className="mb-1 block text-muted">Aggregation</span>
        <select
          className="w-full rounded-lg border border-line bg-ink px-3 py-2"
          value={filters.aggregation}
          onChange={(event) => filters.update('aggregation', event.target.value)}
        >
          <option value="annual">Annual</option>
          <option value="seasonal">Seasonal</option>
        </select>
      </label>
      <label className="text-sm">
        <span className="mb-1 block text-muted">Season</span>
        <select
          className="w-full rounded-lg border border-line bg-ink px-3 py-2"
          value={filters.season}
          disabled={filters.aggregation !== 'seasonal'}
          onChange={(event) => filters.update('season', event.target.value)}
        >
          {seasons.map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </label>
      <label className="text-sm">
        <span className="mb-1 block text-muted">Region</span>
        <select
          className="w-full rounded-lg border border-line bg-ink px-3 py-2"
          value={filters.regionId}
          onChange={(event) => filters.update('region', event.target.value)}
        >
          <option value="">Myanmar</option>
          {regions.data?.regions
            .filter((region) => region.level === 'ADM1')
            .map((region) => (
              <option key={region.id} value={region.id}>
                {region.name}
              </option>
            ))}
        </select>
      </label>
    </form>
  )
}
