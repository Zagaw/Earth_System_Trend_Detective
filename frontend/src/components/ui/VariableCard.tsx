import type { VariableInfo } from '../../types/api'

const tones: Record<VariableInfo['id'], string> = {
  precipitation: 'text-rain',
  temperature: 'text-heat',
  relative_humidity: 'text-humid',
}

export function VariableCard({ variable }: { variable: VariableInfo }) {
  return (
    <article className="rounded-2xl border border-line bg-panel p-5">
      <p className={`text-sm font-medium ${tones[variable.id]}`}>{variable.label}</p>
      <h2 className="mt-2 text-xl font-semibold text-white">{variable.source_parameter}</h2>
      <dl className="mt-4 space-y-3 text-sm">
        <div>
          <dt className="text-muted">Source unit</dt>
          <dd>{variable.source_unit}</dd>
        </div>
        <div>
          <dt className="text-muted">Analysis unit</dt>
          <dd>{variable.analysis_unit}</dd>
        </div>
        <div>
          <dt className="text-muted">Aggregation</dt>
          <dd>{variable.aggregation_rule}</dd>
        </div>
      </dl>
      <p className="mt-4 text-xs text-muted">Verified {variable.verified_on}. No climate value is shown here.</p>
    </article>
  )
}
