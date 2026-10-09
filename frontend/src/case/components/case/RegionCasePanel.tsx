import type { ReactNode } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { CloudRain, Droplets, Thermometer, X, type LucideIcon } from 'lucide-react'
import { VARIABLE_NAME, decadePhrase, decadeUnit, digitsFor, formatMeasure, unitShort } from '../../lib/format'
import type { CaseFile, PlaceRecord, VariableId } from '../../types'
import { PValueGauge } from '../viz/PValueGauge'
import { RainBars } from '../viz/RainBars'
import { Stripes } from '../viz/Stripes'
import { TrendChart } from '../viz/TrendChart'
import { CountUp } from '../viz/CountUp'
import { VerdictStamp } from './VerdictStamp'

const icons: Record<VariableId, LucideIcon> = {
  temperature: Thermometer,
  precipitation: CloudRain,
  relative_humidity: Droplets,
}

function Clue({ title, hint, children }: { title: string; hint: string; children: ReactNode }) {
  return (
    <article className="rounded-xl border border-line bg-navy/60 p-3">
      <div className="flex items-center justify-between gap-2">
        <h4 className="text-xs tracking-wide text-gold uppercase">{title}</h4>
        <button type="button" className="text-xs text-muted" title={hint} aria-label={hint}>
          i
        </button>
      </div>
      <div className="mt-2 text-sm text-ink">{children}</div>
    </article>
  )
}

export function RegionCasePanel({
  file,
  variable,
  place,
  rankedIds,
  onClose,
  onNext,
  onCompare,
}: {
  file: CaseFile
  variable: VariableId
  place: PlaceRecord
  rankedIds: string[]
  onClose: () => void
  onNext: () => void
  onCompare: () => void
}) {
  const reduce = useReducedMotion()
  const Icon = icons[variable]
  const unit = unitShort(variable)
  const digits = variable === 'precipitation' ? 0 : 1
  return (
    <motion.aside
      initial={reduce ? false : { x: 36, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={reduce ? { duration: 0 } : { type: 'spring', stiffness: 280, damping: 28 }}
      className="fixed inset-x-0 bottom-0 z-30 max-h-[86vh] overflow-y-auto rounded-t-3xl border border-line bg-surface p-4 shadow-2xl md:static md:max-h-[760px] md:rounded-2xl"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="flex items-center gap-2 text-sm text-muted">
            <Icon size={16} className="text-gold" aria-hidden="true" />
            {VARIABLE_NAME[variable]}
          </p>
          <h3 className="font-display text-2xl font-bold">{place.geography_name}</h3>
        </div>
        <button type="button" onClick={onClose} aria-label="Close region case" className="rounded-full border border-line p-2">
          <X size={16} />
        </button>
      </div>
      <div className="mt-4">
        <VerdictStamp status={place.trend_status} marked />
      </div>
      <div className="mt-4">
        {variable === 'precipitation' ? (
          <RainBars series={place.series} reference={file.anomaly_reference} />
        ) : (
          <Stripes series={place.series} variable={variable} reference={file.anomaly_reference} />
        )}
      </div>
      <div className="mt-4">
        <TrendChart
          place={place}
          variable={variable}
          baselineStart={file.baseline_start_year}
          baselineEnd={file.baseline_end_year}
          comparisonStart={file.comparison_start_year}
          comparisonEnd={file.comparison_end_year}
        />
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <Clue title="What" hint="The climate variable and the unit of the yearly series.">
          {VARIABLE_NAME[variable]} · {file.variables[variable].unit}
        </Clue>
        <Clue title="How much" hint="Sen's slope rescaled from per year to per 10 years. The test itself is unchanged.">
          <p className="tabular font-display text-xl font-bold">
            <CountUp value={place.slope_per_decade} digits={digitsFor(variable, place.slope_per_decade)} />
          </p>
          <p className="text-muted">{decadeUnit(variable)}</p>
          <p className="mt-1 text-muted">
            {place.slope_text} {place.slope_unit}
          </p>
        </Clue>
        <Clue title="Then vs now" hint="Accepted period means from the API. A window is omitted when fewer than 80% of its years are valid.">
          {place.baseline_mean == null || place.comparison_mean == null ? (
            'One of the two decades does not have enough valid years.'
          ) : (
            <>
              {file.baseline_start_year}–{file.baseline_end_year}: {formatMeasure(place.baseline_mean, digits, unit)}
              <br />
              {file.comparison_start_year}–{file.comparison_end_year}: {formatMeasure(place.comparison_mean, digits, unit)}
            </>
          )}
        </Clue>
        <Clue title="Significant?" hint="Uses the corrected p-value returned by the API. The page does not decide significance itself.">
          <PValueGauge pValue={place.adjusted_p_value} alpha={file.significance_alpha} />
        </Clue>
      </div>
      <article className="mt-4 rounded-xl border border-gold/30 bg-navy/50 p-3">
        <h4 className="font-display text-sm font-semibold text-gold">Detective's note</h4>
        <p className="mt-2 text-sm leading-6 text-ink">{place.interpretation}</p>
      </article>
      <div className="mt-4 flex flex-wrap gap-2">
        <button type="button" onClick={onCompare} className="rounded-full bg-gold px-4 py-2 text-sm font-semibold text-navy">
          Compare with…
        </button>
        <button
          type="button"
          onClick={onNext}
          disabled={rankedIds.length < 2}
          className="rounded-full border border-line px-4 py-2 text-sm disabled:opacity-40"
        >
          Next region
        </button>
      </div>
      <p className="mt-3 text-xs text-muted">{decadePhrase(variable, place.slope_per_decade)}</p>
    </motion.aside>
  )
}
