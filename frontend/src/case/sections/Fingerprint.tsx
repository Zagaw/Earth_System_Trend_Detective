import { useState } from 'react'
import { useCase } from '../context/CaseContext'
import { MyanmarMap } from '../components/map/MyanmarMap'
import { VARIABLE_NAME, VARIABLE_ORDER, decadePhrase, directionWords, verdictPlain } from '../lib/format'
import { oppositeRegionIds, placeFor } from '../lib/twins'

export function Fingerprint() {
  const { file, boundaries, hoverRegionId, setHoverRegionId, setVariable, setSection, setSelectedRegionId } = useCase()
  const [hover, setHover] = useState<string | null>(null)
  if (!file || !boundaries) return null
  const gold = oppositeRegionIds(file)
  const activeHover = hover ?? hoverRegionId
  const note = activeHover
    ? VARIABLE_ORDER.map((variable) => {
        const place = placeFor(file, variable, activeHover)
        if (!place) return ''
        const words = directionWords(variable, place.sen_slope)
        const verdict = place.trend_status.startsWith('significant') ? 'significant' : verdictPlain(place.trend_status).toLowerCase()
        return `${words} ${decadePhrase(variable, place.slope_per_decade)} (${verdict})`
      }).join(', ')
    : ''
  const name = file.regions.find((region) => region.id === activeHover)?.name

  return (
    <section>
      <h2 className="font-display text-3xl font-bold">Fingerprint</h2>
      <p className="mt-2 max-w-3xl text-sm text-muted">
        {gold.size
          ? 'Regions where variables move in different directions are outlined in gold.'
          : 'No region has opposite significant trends across variables in this period.'}
      </p>
      <div className="mt-4 grid gap-3 lg:grid-cols-3">
        {VARIABLE_ORDER.map((variable) => (
          <article key={variable} className="rounded-2xl border border-line bg-surface p-3">
            <h3 className="mb-2 font-display font-semibold">{VARIABLE_NAME[variable]}</h3>
            <div className="h-[360px]">
              <MyanmarMap
                boundaries={boundaries}
                places={file.variables[variable].regions}
                variable={variable}
                mode="trend"
                year={file.end_year}
                hoverId={activeHover}
                goldIds={gold}
                showLabels={false}
                onHover={(id) => {
                  setHover(id)
                  setHoverRegionId(id)
                }}
                onSelect={(id) => {
                  setVariable(variable)
                  setSelectedRegionId(id)
                  setSection('map')
                }}
              />
            </div>
          </article>
        ))}
      </div>
      <p className="mt-4 min-h-12 rounded-xl border border-line bg-surface px-3 py-2 text-sm">
        {name ? (
          <>
            <strong>{name}:</strong> {note}
          </>
        ) : (
          'Hover a region to read temperature, rainfall, and humidity together.'
        )}
      </p>
    </section>
  )
}
