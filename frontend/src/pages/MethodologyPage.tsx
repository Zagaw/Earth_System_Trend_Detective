import { useAnalysisConfig, useMetadata } from '../hooks/useClimateCatalog'

export function MethodologyPage() {
  const metadata = useMetadata()
  const config = useAnalysisConfig()

  return (
    <section className="max-w-3xl space-y-8">
      <div>
        <h2 className="text-3xl font-semibold text-white">Methodology and data</h2>
        <p className="mt-3 text-muted">
          Units on this page come from the API catalogue, which was checked against live NASA POWER
          responses on 9 October 2026.
        </p>
      </div>

      {metadata.isLoading || config.isLoading ? <p>Loading methodology records…</p> : null}
      {metadata.isError || config.isError ? (
        <p>Methodology records could not be loaded from the API.</p>
      ) : null}

      {metadata.data
        ? metadata.data.variables.map((variable) => (
            <article key={variable.id} className="rounded-2xl border border-line bg-panel p-5">
              <h3 className="text-lg font-semibold text-white">{variable.label}</h3>
              <p className="mt-2 text-sm text-muted">{variable.temporal_meaning}</p>
              <p className="mt-3 text-sm">
                {variable.source_parameter} · source {variable.source_unit} · analysis{' '}
                {variable.analysis_unit} · slope {variable.slope_unit}
              </p>
              {variable.conversion ? (
                <p className="mt-2 font-mono text-sm text-accent">{variable.conversion}</p>
              ) : null}
            </article>
          ))
        : null}

      {config.data ? (
        <article className="rounded-2xl border border-line bg-panel p-5 text-sm">
          <h3 className="text-lg font-semibold text-white">Statistical settings</h3>
          <p className="mt-2">{config.data.note}</p>
          <ul className="mt-4 space-y-1 text-muted">
            <li>Alpha {config.data.significance_alpha}</li>
            <li>Trend method {config.data.trend_method}</li>
            <li>Test {config.data.significance_test}</li>
            <li>Multiple testing {config.data.multiple_testing}</li>
            <li>Minimum valid years {config.data.minimum_valid_years}</li>
            <li>Planned seasons {config.data.seasons_planned.join(', ')}</li>
            <li>
              Calculations implemented: {config.data.calculations_implemented ? 'yes' : 'no'}
            </li>
          </ul>
        </article>
      ) : null}

      {metadata.data ? (
        <div>
          <h3 className="text-lg font-semibold text-white">Not done yet</h3>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-muted">
            {metadata.data.incomplete.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  )
}
