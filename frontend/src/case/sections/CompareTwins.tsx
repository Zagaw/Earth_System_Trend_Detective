import { useCase } from '../context/CaseContext'
import { CompareChart } from '../components/compare/CompareChart'
import { OppositeBanner } from '../components/compare/OppositeBanner'
import { RankingTable } from '../components/compare/RankingTable'
import { MyanmarMap } from '../components/map/MyanmarMap'
import { VerdictStamp } from '../components/case/VerdictStamp'
import { downloadText, rankingCsv } from '../lib/csv'
import { VARIABLE_NAME, decadePhrase } from '../lib/format'
import { isOpposite, suggestTwins } from '../lib/twins'

export function CompareTwins() {
  const state = useCase()
  const { file, boundaries, variable } = state
  if (!file || !boundaries) return null
  const places = file.variables[variable].regions
  const left = places.find((place) => place.geography_id === state.compareA)
  const right = places.find((place) => place.geography_id === state.compareB)
  const opposite = isOpposite(left, right)

  return (
    <section className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="font-display text-3xl font-bold">Compare twins</h2>
          <p className="mt-1 text-sm text-muted">First map click sets region A. The next click sets region B.</p>
        </div>
        <button
          type="button"
          className="rounded-full bg-gold px-4 py-2 text-sm font-semibold text-navy"
          onClick={() => {
            const pair = suggestTwins(places)
            if (!pair) {
              state.setTwinNote('No opposite significant pair found for this variable.')
              return
            }
            state.setTwinNote('')
            state.setCompareA(pair[0].geography_id)
            state.setCompareB(pair[1].geography_id)
          }}
        >
          Suggest twins
        </button>
      </div>
      {state.twinNote ? <p className="text-sm text-gold">{state.twinNote}</p> : null}
      <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
        <div className="h-[320px] overflow-hidden rounded-2xl border border-line bg-[#0B1228]">
          <MyanmarMap
            boundaries={boundaries}
            places={places}
            variable={variable}
            mode="trend"
            year={file.end_year}
            marks={[
              ...(state.compareA ? [{ id: state.compareA, color: '#FB923C' }] : []),
              ...(state.compareB ? [{ id: state.compareB, color: '#2DD4BF' }] : []),
            ]}
            showLabels={false}
            onSelect={state.assignCompare}
          />
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <Picker label="Region A" value={state.compareA} places={places} onChange={state.setCompareA} />
          <Picker label="Region B" value={state.compareB} places={places} onChange={state.setCompareB} />
        </div>
      </div>
      {!left || !right ? (
        <p className="rounded-2xl border border-dashed border-line p-6 text-muted">Pick two regions to compare.</p>
      ) : (
        <>
          {opposite ? <OppositeBanner variable={variable} left={left} right={right} /> : null}
          <div className="rounded-2xl border border-line bg-surface p-4">
            <CompareChart variable={variable} left={left} right={right} />
            <p className="text-xs text-muted">
              <span className="text-[#FB923C]">{left.geography_name}</span> and{' '}
              <span className="text-[#2DD4BF]">{right.geography_name}</span>. Dashed lines are Sen's slopes. {VARIABLE_NAME[variable]}.
            </p>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <TwinCard name={left.geography_name} status={left.trend_status} phrase={decadePhrase(variable, left.slope_per_decade)} />
            <TwinCard name={right.geography_name} status={right.trend_status} phrase={decadePhrase(variable, right.slope_per_decade)} />
          </div>
        </>
      )}
      <div className="rounded-2xl border border-line bg-surface p-4">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="font-display text-lg font-bold">Ranking</h3>
          <button
            type="button"
            className="text-sm text-gold"
            onClick={() => downloadText(`earthtrend-${variable}-ranking.csv`, rankingCsv(file, variable, places))}
          >
            Download CSV
          </button>
        </div>
        <RankingTable
          rows={places}
          variable={variable}
          hoverId={state.hoverRegionId}
          onHover={state.setHoverRegionId}
          onSelect={(id) => {
            state.setSelectedRegionId(id)
            state.setSection('map')
          }}
        />
      </div>
    </section>
  )
}

function Picker({
  label,
  value,
  places,
  onChange,
}: {
  label: string
  value: string | null
  places: Array<{ geography_id: string; geography_name: string }>
  onChange: (id: string) => void
}) {
  return (
    <label className="block text-sm">
      <span className="text-muted">{label}</span>
      <select
        className="mt-1 w-full rounded-xl border border-line bg-navy px-3 py-2"
        value={value ?? ''}
        onChange={(event) => onChange(event.target.value)}
      >
        <option value="" disabled>
          Choose a region
        </option>
        {places.map((place) => (
          <option key={place.geography_id} value={place.geography_id}>
            {place.geography_name}
          </option>
        ))}
      </select>
    </label>
  )
}

function TwinCard({ name, status, phrase }: { name: string; status: string; phrase: string }) {
  return (
    <article className="rounded-2xl border border-line bg-surface p-4">
      <h3 className="font-display text-xl font-bold">{name}</h3>
      <p className="tabular mt-2 text-sm">{phrase}</p>
      <div className="mt-3">
        <VerdictStamp status={status} />
      </div>
    </article>
  )
}
