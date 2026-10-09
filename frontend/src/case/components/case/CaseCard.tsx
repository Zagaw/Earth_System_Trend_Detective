import { CloudRain, Droplets, Thermometer, type LucideIcon } from 'lucide-react'
import { Check } from 'lucide-react'
import { paint } from '../../lib/colors'
import { VARIABLE_NAME, decadeUnit, digitsFor, directionWords } from '../../lib/format'
import type { PlaceRecord, VariableId } from '../../types'
import { CountUp } from '../viz/CountUp'
import { Sparkline } from '../viz/Sparkline'
import { VerdictStamp } from './VerdictStamp'

const icons: Record<VariableId, LucideIcon> = {
  temperature: Thermometer,
  precipitation: CloudRain,
  relative_humidity: Droplets,
}

export function CaseCard({
  variable,
  place,
  active,
  onSelect,
}: {
  variable: VariableId
  place: PlaceRecord
  active: boolean
  onSelect: () => void
}) {
  const Icon = icons[variable]
  const clues = [
    { label: 'What', done: true },
    { label: 'Where', done: true },
    { label: 'How much', done: place.slope_per_decade != null },
    { label: 'Significant', done: place.trend_status.startsWith('significant') },
  ]
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`rounded-2xl border bg-surface p-4 text-left transition ${
        active ? 'border-gold shadow-[0_0_24px_rgba(251,191,36,0.22)]' : 'border-line hover:border-gold/50'
      }`}
    >
      <div className="flex items-center justify-between gap-3">
        <span className="flex items-center gap-2 font-display text-lg font-semibold">
          <Icon size={18} className="text-gold" aria-hidden="true" />
          {VARIABLE_NAME[variable]}
        </span>
        <VerdictStamp status={place.trend_status} />
      </div>
      <p className="tabular mt-4 font-display text-2xl font-bold text-ink">
        <CountUp value={place.slope_per_decade} digits={digitsFor(variable, place.slope_per_decade)} />
      </p>
      <p className="text-sm text-muted">{decadeUnit(variable)}</p>
      <p className="mt-1 text-sm text-muted">{directionWords(variable, place.sen_slope)}</p>
      <div className="mt-3">
        <Sparkline values={place.series.map((point) => point.value)} color={paint(variable, place.slope_per_decade, Math.abs(place.slope_per_decade ?? 1))} />
      </div>
      <ul className="mt-3 flex flex-wrap gap-2">
        {clues.map((clue) => (
          <li key={clue.label} className="flex items-center gap-1 text-xs text-muted">
            <Check size={12} className={clue.done ? 'text-gold' : 'text-line'} aria-hidden="true" />
            {clue.label}
          </li>
        ))}
      </ul>
    </button>
  )
}
