import { domainMax, paint } from '../lib/colors'
import { VARIABLE_ORDER, directionWords, verdictPlain } from '../lib/format'
import type { PlaceRecord, VariableId } from '../types'
import { useCase } from '../context/CaseContext'
import { CaseCard } from '../components/case/CaseCard'
import { Stripes } from '../components/viz/Stripes'

const order = ['significant_decreasing', 'not_significant', 'significant_increasing', 'insufficient_data']

export function CaseOverview() {
  const { file, variable, setVariable, setSection, setHighlightIds, setMapMode, setSelectedRegionId } = useCase()
  if (!file) return null
  const selected = file.variables[variable]
  const places = selected.regions
  const grouped = new Map<string, PlaceRecord[]>()
  for (const status of order) grouped.set(status, [])
  for (const place of places) {
    const key = grouped.has(place.trend_status) ? place.trend_status : 'insufficient_data'
    grouped.get(key)?.push(place)
  }
  const span = domainMax(places.map((place) => place.slope_per_decade))
  const increasing = grouped.get('significant_increasing') ?? []
  const decreasing = grouped.get('significant_decreasing') ?? []
  const unclear = grouped.get('not_significant') ?? []
  const missing = grouped.get('insufficient_data') ?? []

  return (
    <section className="space-y-8">
      <div className="stars rounded-3xl border border-line p-6">
        <h2 className="max-w-3xl font-display text-4xl font-bold leading-tight">
          Is Myanmar's climate changing? Let's investigate.
        </h2>
        <p className="mt-3 text-muted">25 years of NASA satellite and model data, {file.start_year}–{file.end_year}.</p>
        <div className="mt-6">
          <Stripes series={selected.national.series} variable={variable} reference={file.anomaly_reference} />
        </div>
        <button
          type="button"
          className="mt-6 rounded-full bg-gold px-5 py-2 font-semibold text-navy"
          onClick={() => setSection('map')}
        >
          Start the investigation →
        </button>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        {VARIABLE_ORDER.map((id) => (
          <CaseCard
            key={id}
            variable={id}
            place={file.variables[id].national}
            active={variable === id}
            onSelect={() => setVariable(id)}
          />
        ))}
      </div>

      <div className="rounded-2xl border border-line bg-surface p-5">
        <h3 className="font-display text-xl font-bold">{selected.national.geography_name}</h3>
        <p className="mt-3 text-sm leading-6 text-ink">{selected.national.interpretation}</p>
        <p className="mt-4 text-sm text-muted">
          {increasing.length} regions show a significant increase ({directionWords(variable, 1)}). {decreasing.length}{' '}
          show a significant decrease ({directionWords(variable, -1)}). {unclear.length} show no clear change.
          {missing.length ? ` ${missing.length} do not have enough data.` : ''}
        </p>
        <div className="mt-4 flex h-10 overflow-hidden rounded-full border border-line">
          {order.map((status) => {
            const members = grouped.get(status) ?? []
            if (!members.length) return null
            const sample = status === 'significant_decreasing' ? -span : status === 'significant_increasing' ? span : 0
            return (
              <button
                key={status}
                type="button"
                className="h-full text-[11px] text-navy"
                style={{
                  width: `${(members.length / places.length) * 100}%`,
                  background:
                    status === 'not_significant'
                      ? 'repeating-linear-gradient(45deg, #334155 0 4px, #1e293b 4px 8px)'
                      : status === 'insufficient_data'
                        ? '#334155'
                        : paint(variable as VariableId, sample || 1, span || 1),
                  color: status === 'not_significant' || status === 'insufficient_data' ? '#F8FAFC' : '#070B1F',
                }}
                title={`${verdictPlain(status)}: ${members.map((item) => item.geography_name).join(', ')}`}
                onClick={() => {
                  setHighlightIds(members.map((item) => item.geography_id))
                  setSelectedRegionId(null)
                  setMapMode('trend')
                  setSection('map')
                }}
              >
                {members.length}
              </button>
            )
          })}
        </div>
      </div>
    </section>
  )
}
