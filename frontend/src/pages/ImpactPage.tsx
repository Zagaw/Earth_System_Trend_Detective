import { useQuery } from '@tanstack/react-query'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { FilterBar } from '../components/filters/FilterBar'
import { useAnalysisQuery } from '../hooks/useAnalysisQuery'
import { API_BASE, ApiRequestError, getAnomalies, getImpact } from '../lib/api'

export function ImpactPage() {
  const filters = useAnalysisQuery()
  const impact = useQuery({
    queryKey: ['impact', filters.queryString],
    queryFn: () => getImpact(filters.queryString),
  })
  const anomalies = useQuery({
    queryKey: ['anomalies', filters.queryString],
    queryFn: () => getAnomalies(filters.queryString),
  })

  return (
    <section className="space-y-6">
      <div>
        <h2 className="text-3xl font-semibold text-white">Impact and anomalies</h2>
        <p className="mt-2 max-w-3xl text-muted">
          These figures compare climate periods. They are not measurements of crop loss, health
          impacts, or economic damage.
        </p>
      </div>
      <FilterBar />
      {impact.isLoading ? <p>Calculating indicators…</p> : null}
      {impact.error ? (
        <p className="text-heat">{impact.error instanceof ApiRequestError ? impact.error.message : impact.error.message}</p>
      ) : null}
      {impact.data ? (
        <article className="rounded-2xl border border-line bg-panel p-5">
          <h3 className="text-lg font-semibold text-white">{impact.data.geography_name}</h3>
          <p className="mt-3 text-sm leading-6">{impact.data.interpretation}</p>
          <dl className="mt-4 grid gap-4 text-sm md:grid-cols-3">
            <div>
              <dt className="text-muted">Baseline mean</dt>
              <dd>
                {format(impact.data.baseline_mean)} {impact.data.unit} ({impact.data.baseline_start_year}–
                {impact.data.baseline_end_year})
              </dd>
            </div>
            <div>
              <dt className="text-muted">Comparison mean</dt>
              <dd>
                {format(impact.data.comparison_mean)} {impact.data.unit} ({impact.data.comparison_start_year}–
                {impact.data.comparison_end_year})
              </dd>
            </div>
            <div>
              <dt className="text-muted">Absolute difference</dt>
              <dd>
                {format(impact.data.absolute_difference)} {impact.data.unit}
              </dd>
            </div>
            <div>
              <dt className="text-muted">Area with significant increase</dt>
              <dd>{percent(impact.data.increasing_area_fraction)} of tested cells</dd>
            </div>
            <div>
              <dt className="text-muted">Area with significant decrease</dt>
              <dd>{percent(impact.data.decreasing_area_fraction)} of tested cells</dd>
            </div>
            <div>
              <dt className="text-muted">Years above baseline 90th percentile</dt>
              <dd>{impact.data.years_above_baseline_p90 ?? 'n/a'}</dd>
            </div>
          </dl>
          <p className="mt-4 text-sm text-muted">{impact.data.limitation}</p>
          <a className="mt-3 inline-block text-sm text-accent" href={`${API_BASE}/export/impact.csv?${filters.queryString}`}>
            Download impact CSV
          </a>
        </article>
      ) : null}
      {anomalies.data ? (
        <article className="h-80 rounded-2xl border border-line bg-panel p-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={anomalies.data.data}>
              <CartesianGrid stroke="#314038" vertical={false} />
              <XAxis dataKey="year" stroke="#93a79b" minTickGap={24} />
              <YAxis stroke="#93a79b" width={56} />
              <Tooltip contentStyle={{ background: '#18211c', border: '1px solid #314038' }} />
              <Bar dataKey="anomaly" fill="#e0a15a" />
            </BarChart>
          </ResponsiveContainer>
        </article>
      ) : null}
    </section>
  )
}

function format(value: number | null) {
  return value == null ? 'n/a' : value.toFixed(2)
}

function percent(value: number | null) {
  return value == null ? 'n/a' : `${Math.round(value * 100)}%`
}
