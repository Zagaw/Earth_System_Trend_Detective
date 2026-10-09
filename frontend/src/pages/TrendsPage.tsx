import { useQuery } from '@tanstack/react-query'
import { TimeSeriesChart } from '../components/charts/TimeSeriesChart'
import { FilterBar } from '../components/filters/FilterBar'
import { StatusPill } from '../components/ui/StatusPill'
import { useAnalysisQuery } from '../hooks/useAnalysisQuery'
import { API_BASE, ApiRequestError, getTimeSeries, getTrend } from '../lib/api'

export function TrendsPage() {
  const filters = useAnalysisQuery()
  const trend = useQuery({
    queryKey: ['trend', filters.queryString],
    queryFn: () => getTrend(filters.queryString),
  })
  const series = useQuery({
    queryKey: ['series', filters.queryString],
    queryFn: () => getTimeSeries(filters.queryString),
  })

  return (
    <section className="space-y-6">
      <div>
        <h2 className="text-3xl font-semibold text-white">Trend analysis</h2>
        <p className="mt-2 text-muted">
          Sen’s slope is fitted to the aggregated series. Significance uses Mann–Kendall, with a
          Hamed–Rao correction when the residuals are strongly autocorrelated.
        </p>
      </div>
      <FilterBar />
      {trend.isLoading ? <p>Calculating the trend…</p> : null}
      {trend.error ? <p className="text-heat">{messageOf(trend.error)}</p> : null}
      {trend.data ? (
        <article className="rounded-2xl border border-line bg-panel p-5">
          <div className="flex flex-wrap items-center gap-3">
            <h3 className="text-xl font-semibold text-white">{trend.data.geography_name}</h3>
            <StatusPill status={trend.data.trend_status} />
          </div>
          <dl className="mt-4 grid gap-4 text-sm md:grid-cols-3">
            <div>
              <dt className="text-muted">Sen’s slope</dt>
              <dd>
                {trend.data.slope_text} {trend.data.slope_unit}
              </dd>
            </div>
            <div>
              <dt className="text-muted">95% slope interval</dt>
              <dd>
                {trend.data.confidence_interval_95
                  ? trend.data.confidence_interval_95.map((value) => value.toFixed(3)).join(' to ')
                  : 'Unavailable'}
              </dd>
            </div>
            <div>
              <dt className="text-muted">p-value / adjusted p</dt>
              <dd>
                {formatP(trend.data.p_value)} / {formatP(trend.data.adjusted_p_value)}
              </dd>
            </div>
            <div>
              <dt className="text-muted">Effective period</dt>
              <dd>
                {trend.data.effective_start_year ?? '—'}–{trend.data.effective_end_year ?? '—'}
              </dd>
            </div>
            <div>
              <dt className="text-muted">Method</dt>
              <dd>{trend.data.test_method}</dd>
            </div>
            <div>
              <dt className="text-muted">Multiple testing</dt>
              <dd>{trend.data.multiple_testing_method}</dd>
            </div>
          </dl>
          <p className="mt-4 text-sm leading-6">{trend.data.interpretation}</p>
        </article>
      ) : null}
      {series.data ? (
        <article className="rounded-2xl border border-line bg-panel p-5">
          <TimeSeriesChart points={series.data.data} trendLine={series.data.trend_line} unit={series.data.unit} />
          <a className="mt-3 inline-block text-sm text-accent" href={`${API_BASE}/export/timeseries.csv?${filters.queryString}`}>
            Download this series
          </a>
        </article>
      ) : null}
    </section>
  )
}

function formatP(value: number | null) {
  return value == null ? 'n/a' : value.toFixed(4)
}

function messageOf(error: Error) {
  return error instanceof ApiRequestError ? error.message : error.message
}
