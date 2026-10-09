import { useMemo } from 'react'
import { useCase } from '../context/CaseContext'
import { MapLegend } from '../components/map/MapLegend'
import { MyanmarMap } from '../components/map/MyanmarMap'
import { YearSlider } from '../components/map/YearSlider'
import { VariablePills } from '../components/layout/Header'
import { RegionCasePanel } from '../components/case/RegionCasePanel'
import { DivergingBars } from '../components/viz/DivergingBars'
import { domainMax } from '../lib/colors'
import {
  decadePhrase,
  decadeUnit,
  directionWords,
  formatSigned,
  isFiniteNumber,
  metricValue,
  unitShort,
  verdictPlain,
} from '../lib/format'
import type { MapMode, PlaceRecord, VariableId } from '../types'

function ranked(places: PlaceRecord[], direction: 'up' | 'down') {
  return [...places]
    .filter((place) => isFiniteNumber(place.slope_per_decade))
    .sort((left, right) =>
      direction === 'up'
        ? (right.slope_per_decade ?? 0) - (left.slope_per_decade ?? 0)
        : (left.slope_per_decade ?? 0) - (right.slope_per_decade ?? 0),
    )
    .slice(0, 3)
}

function extreme(places: PlaceRecord[], year: number, direction: 'high' | 'low') {
  const scored = places
    .map((place) => ({ place, anomaly: place.series.find((point) => point.year === year)?.anomaly ?? null }))
    .filter((item) => isFiniteNumber(item.anomaly))
  scored.sort((left, right) =>
    direction === 'high' ? (right.anomaly ?? 0) - (left.anomaly ?? 0) : (left.anomaly ?? 0) - (right.anomaly ?? 0),
  )
  return scored[0]
}

const yearLabel: Record<VariableId, [string, string]> = {
  temperature: ['warmest', 'coolest'],
  precipitation: ['wettest', 'driest'],
  relative_humidity: ['most humid', 'least humid'],
}

export function InvestigationMap() {
  const state = useCase()
  const { file, boundaries, variable, mapMode, year, setYear, playing, setPlaying, setMapMode } = state
  const places = file?.variables[variable].regions ?? []
  const order = useMemo(
    () =>
      [...places].sort((left, right) => (right.slope_per_decade ?? Number.NEGATIVE_INFINITY) - (left.slope_per_decade ?? Number.NEGATIVE_INFINITY)),
    [places],
  )
  if (!file || !boundaries) return null
  const selected = places.find((place) => place.geography_id === state.selectedRegionId) ?? null
  const span = domainMax(places.map((place) => metricValue(place, mapMode, year)))
  const unit = mapMode === 'trend' ? decadeUnit(variable) : mapMode === 'change' ? file.variables[variable].unit : `${unitShort(variable)} anomaly`
  const bars = places
    .map((place) => ({
      id: place.geography_id,
      name: place.geography_name,
      value: metricValue(place, mapMode, year),
      status: place.trend_status,
    }))
    .sort((left, right) => (right.value ?? Number.NEGATIVE_INFINITY) - (left.value ?? Number.NEGATIVE_INFINITY))

  const open = (id: string) => {
    state.setSelectedRegionId(id)
    state.setHighlightIds([])
  }

  return (
    <section className="grid items-start gap-4 lg:grid-cols-[minmax(0,1.7fr)_minmax(300px,1fr)]">
      <div>
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <div className="flex rounded-full border border-line p-1 text-sm">
            {(
              [
                ['trend', 'Trend'],
                ['year', 'Year-by-year'],
                ['change', 'Then vs now'],
              ] as Array<[MapMode, string]>
            ).map(([mode, label]) => (
              <button
                key={mode}
                type="button"
                onClick={() => setMapMode(mode)}
                className={`rounded-full px-3 py-1 ${mapMode === mode ? 'bg-gold text-navy' : 'text-muted'}`}
              >
                {label}
              </button>
            ))}
          </div>
          <VariablePills />
        </div>
        <div data-tour="map" className="h-[560px] overflow-hidden rounded-2xl border border-line bg-[#0B1228]">
          <MyanmarMap
            boundaries={boundaries}
            places={places}
            variable={variable}
            mode={mapMode}
            year={year}
            selectedId={state.selectedRegionId}
            hoverId={state.hoverRegionId}
            highlightIds={state.highlightIds}
            showLabels={mapMode === 'trend'}
            showRaindrops={variable === 'precipitation' && mapMode === 'trend'}
            onHover={state.setHoverRegionId}
            onSelect={open}
          />
        </div>
        <MapLegend variable={variable} mode={mapMode} span={span} unit={unit} reference={file.anomaly_reference} />
        {mapMode === 'year' ? (
          <YearSlider
            year={year}
            start={file.start_year}
            end={file.end_year}
            playing={playing}
            onYear={setYear}
            onToggle={() => setPlaying(!playing)}
          />
        ) : null}
        {state.hoverRegionId ? <HoverNote places={places} id={state.hoverRegionId} variable={variable} mode={mapMode} year={year} /> : null}
      </div>
      <div>
        {selected ? (
          <RegionCasePanel
            file={file}
            variable={variable}
            place={selected}
            rankedIds={order.map((place) => place.geography_id)}
            onClose={() => state.setSelectedRegionId(null)}
            onCompare={() => {
              state.setCompareA(selected.geography_id)
              state.setCompareB(null)
              state.setSection('compare')
            }}
            onNext={() => {
              const index = order.findIndex((place) => place.geography_id === selected.geography_id)
              const next = order[(index + 1) % order.length]
              if (next) state.setSelectedRegionId(next.geography_id)
            }}
          />
        ) : (
          <ClueBoard places={places} variable={variable} mode={mapMode} year={year} bars={bars} hoverId={state.hoverRegionId} onHover={state.setHoverRegionId} onSelect={open} reference={file.anomaly_reference} />
        )}
      </div>
    </section>
  )
}

function HoverNote({
  places,
  id,
  variable,
  mode,
  year,
}: {
  places: PlaceRecord[]
  id: string
  variable: VariableId
  mode: MapMode
  year: number
}) {
  const place = places.find((item) => item.geography_id === id)
  if (!place) return null
  const value = metricValue(place, mode, year)
  const phrase =
    mode === 'trend'
      ? `${decadePhrase(variable, value)} (${directionWords(variable, place.sen_slope)})`
      : isFiniteNumber(value)
        ? `${formatSigned(value, 1)} ${mode === 'year' ? 'anomaly' : unitShort(variable)}`
        : 'no value for this view'
  return (
    <p className="mt-3 rounded-xl border border-line bg-surface px-3 py-2 text-sm">
      <strong>{place.geography_name}</strong> · {phrase} · Verdict: {verdictPlain(place.trend_status)}. Select the region for the full case.
    </p>
  )
}

function ClueBoard({
  places,
  variable,
  mode,
  year,
  bars,
  hoverId,
  onHover,
  onSelect,
  reference,
}: {
  places: PlaceRecord[]
  variable: VariableId
  mode: MapMode
  year: number
  bars: Array<{ id: string; name: string; value: number | null; status: string }>
  hoverId: string | null
  onHover: (id: string | null) => void
  onSelect: (id: string) => void
  reference: string
}) {
  if (mode === 'year') {
    const high = extreme(places, year, 'high')
    const low = extreme(places, year, 'low')
    const [highWord, lowWord] = yearLabel[variable]
    return (
      <div className="space-y-4 rounded-2xl border border-line bg-surface p-4">
        <h3 className="font-display text-lg font-bold">{year}</h3>
        <ExtremeCard title={`This year's ${highWord} region`} place={high?.place} anomaly={high?.anomaly ?? null} unit={unitShort(variable)} reference={reference} onSelect={onSelect} />
        <ExtremeCard title={`This year's ${lowWord} region`} place={low?.place} anomaly={low?.anomaly ?? null} unit={unitShort(variable)} reference={reference} onSelect={onSelect} />
        <DivergingBars items={bars} variable={variable} hoverId={hoverId} onHover={onHover} onSelect={onSelect} hatch={false} caption={(item) => `${item.name}: ${isFiniteNumber(item.value) ? formatSigned(item.value, 1) : 'no value'} anomaly`} />
      </div>
    )
  }
  return (
    <div className="space-y-4 rounded-2xl border border-line bg-surface p-4">
      <RankList title="Top 3 strongest increases" rows={ranked(places, 'up')} variable={variable} onHover={onHover} onSelect={onSelect} />
      <RankList title="Top 3 strongest decreases" rows={ranked(places, 'down')} variable={variable} onHover={onHover} onSelect={onSelect} />
      <DivergingBars items={bars} variable={variable} hoverId={hoverId} onHover={onHover} onSelect={onSelect} hatch />
    </div>
  )
}

function RankList({
  title,
  rows,
  variable,
  onHover,
  onSelect,
}: {
  title: string
  rows: PlaceRecord[]
  variable: VariableId
  onHover: (id: string | null) => void
  onSelect: (id: string) => void
}) {
  const span = domainMax(rows.map((row) => row.slope_per_decade))
  return (
    <div>
      <h3 className="text-sm font-semibold">{title}</h3>
      <div className="mt-2 space-y-2">
        {rows.map((row) => (
          <button
            key={row.geography_id}
            type="button"
            className="block w-full rounded-xl border border-line px-3 py-2 text-left"
            onMouseEnter={() => onHover(row.geography_id)}
            onMouseLeave={() => onHover(null)}
            onClick={() => onSelect(row.geography_id)}
          >
            <span className="flex items-center justify-between gap-2 text-sm">
              <span>{row.geography_name}</span>
              <span className="tabular text-muted">{decadePhrase(variable, row.slope_per_decade)}</span>
            </span>
            <span className="mt-2 block h-1.5 rounded-full bg-line">
              <span
                className="block h-1.5 rounded-full"
                style={{
                  width: `${span ? (Math.abs(row.slope_per_decade ?? 0) / span) * 100 : 0}%`,
                  background: row.trend_status === 'insufficient_data' ? '#334155' : '#FBBF24',
                }}
              />
            </span>
            <span className="mt-1 block text-xs text-muted">{verdictPlain(row.trend_status)}</span>
          </button>
        ))}
      </div>
    </div>
  )
}

function ExtremeCard({
  title,
  place,
  anomaly,
  unit,
  reference,
  onSelect,
}: {
  title: string
  place?: PlaceRecord
  anomaly: number | null
  unit: string
  reference: string
  onSelect: (id: string) => void
}) {
  if (!place || !isFiniteNumber(anomaly)) return <p className="text-sm text-muted">No region has a value for this year.</p>
  return (
    <button type="button" className="block w-full rounded-xl border border-line p-3 text-left" onClick={() => onSelect(place.geography_id)}>
      <p className="text-xs text-muted">{title}</p>
      <p className="mt-1 font-display text-lg font-bold">{place.geography_name}</p>
      <p className="tabular text-sm text-muted">
        {formatSigned(anomaly, 2)} {unit} vs {reference}
      </p>
    </button>
  )
}
