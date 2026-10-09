import { useQuery, useQueries } from '@tanstack/react-query'
import { TimeSeriesChart } from '../components/charts/TimeSeriesChart'
import { FilterBar } from '../components/filters/FilterBar'
import { StatusPill } from '../components/ui/StatusPill'
import { useMetadata } from '../hooks/useClimateCatalog'
import { queryForVariable, useAnalysisQuery, variables } from '../hooks/useAnalysisQuery'
import { API_BASE, ApiRequestError, getTimeSeries, getTrend } from '../lib/api'

export function DashboardPage() {
  const metadata = useMetadata()
  const filters = useAnalysisQuery()
  const summaries = useQueries({
    queries: variables.map((variable) => ({
      queryKey: ['trend', queryForVariable(filters.queryString, variable)],
      queryFn: () => getTrend(queryForVariable(filters.queryString, variable)),
    })),
  })
  const series = useQuery({
    queryKey: ['series', filters.queryString],
    queryFn: () => getTimeSeries(filters.queryString),
  })

  return (
    <section className="space-y-6">
      <div>
        <h2 className="text-3xl font-semibold text-white">Myanmar climate trends</h2>
        <p className="mt-2 max-w-3xl text-muted">
          National and state/region results are calculated from NASA POWER. Cards show the selected
          period for each variable. The chart follows the variable filter.
        </p>
      </div>
      <FilterBar />
      {metadata.data?.study_grid_status === 'not_ingested' ? (
        <p className="rounded-xl border border-line bg-panel p-4">
          The study grid is not ingested yet. From the backend folder, run python -m app.cli ingest.
        </p>
      ) : null}
      <div className="grid gap-4 lg:grid-cols-3">
        {summaries.map((summary, index) => (
          <article key={variables[index]} className="rounded-2xl border border-line bg-panel p-5">
            <p className="text-sm text-muted">{variables[index].replaceAll('_', ' ')}</p>
            {summary.isLoading ? <p className="mt-3">Calculating…</p> : null}
            {summary.error ? <ErrorText error={summary.error} /> : null}
            {summary.data ? (
              <>
                <p className="mt-3 text-3xl font-semibold text-white">
                  {summary.data.slope_text}
                  <span className="ml-2 text-base font-normal text-muted">{summary.data.slope_unit}</span>
                </p>
                <div className="mt-3">
                  <StatusPill status={summary.data.trend_status} />
                </div>
                <p className="mt-3 text-sm text-muted">
                  {summary.data.valid_years} of {summary.data.expected_years} valid years
                  {summary.data.coverage_fraction != null
                    ? ` · ${Math.round(summary.data.coverage_fraction * 100)}% coverage`
                    : ''}
                </p>
              </>
            ) : null}
          </article>
        ))}
      </div>
      <article className="rounded-2xl border border-line bg-panel p-5">
        <div className="mb-4 flex items-center justify-between gap-3">
          <h3 className="text-lg font-semibold text-white">
            {series.data?.region_name ?? 'Selected region'} · {series.data?.unit ?? ''}
          </h3>
          <a className="text-sm text-accent" href={`${API_BASE}/export/timeseries.csv?${filters.queryString}`}>
            Download CSV
          </a>
        </div>
        {series.isLoading ? <p>Loading the time series…</p> : null}
        {series.error ? <ErrorText error={series.error} /> : null}
        {series.data ? (
          <TimeSeriesChart points={series.data.data} trendLine={series.data.trend_line} unit={series.data.unit} />
        ) : null}
      </article>
    </section>
  )
}

function ErrorText({ error }: { error: Error }) {
  const message = error instanceof ApiRequestError ? error.message : error.message
  return <p className="mt-3 text-sm text-heat">{message}</p>
}
