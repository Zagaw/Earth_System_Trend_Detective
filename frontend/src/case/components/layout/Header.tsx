import { CloudRain, Droplets, HelpCircle, Thermometer, type LucideIcon } from 'lucide-react'
import { useState } from 'react'
import { VARIABLE_NAME, VARIABLE_ORDER } from '../../lib/format'
import type { VariableId } from '../../types'
import { useCase } from '../../context/CaseContext'

const icons: Record<VariableId, LucideIcon> = {
  temperature: Thermometer,
  precipitation: CloudRain,
  relative_humidity: Droplets,
}

export function VariablePills() {
  const { variable, setVariable } = useCase()
  return (
    <div data-tour="cases" className="flex flex-wrap gap-2">
      {VARIABLE_ORDER.map((id, index) => {
        const Icon = icons[id]
        const active = variable === id
        return (
          <button
            key={id}
            type="button"
            onClick={() => setVariable(id)}
            className={`flex items-center gap-2 rounded-full px-3 py-1.5 text-sm ${
              active ? 'bg-gold text-navy' : 'border border-line text-ink'
            }`}
          >
            <Icon size={15} aria-hidden="true" />
            {VARIABLE_NAME[id]}
            <span className="text-[10px] opacity-70">{index + 1}</span>
          </button>
        )
      })}
    </div>
  )
}

export function Header() {
  const { file, variable, setSection, setTourStep } = useCase()
  const [help, setHelp] = useState(false)
  const coverage = file?.variables[variable].national.coverage_fraction
  return (
    <header className="stars sticky top-0 z-40 border-b border-line bg-navy/90 backdrop-blur">
      <div className="flex flex-wrap items-center gap-3 px-4 py-3">
        <div className="mr-auto flex items-center gap-3">
          <svg width="28" height="28" viewBox="0 0 28 28" aria-hidden="true">
            <path d="M14 2l2.4 7.2H24l-6 4.4 2.3 7.2L14 16.6 7.7 20.8 10 13.6 4 9.2h7.6z" fill="#FBBF24" />
          </svg>
          <div>
            <p className="text-[10px] tracking-[0.18em] text-gold uppercase">Star Devs</p>
            <h1 className="font-display text-lg leading-5 font-bold">EarthTrend Myanmar</h1>
          </div>
        </div>
        <VariablePills />
        <span className="rounded-full border border-line px-3 py-1 text-xs text-muted" title="Share of years with a valid national average">
          {file ? `${file.start_year}–${file.end_year}` : '2001–2025'}
          {coverage == null ? '' : ` · ${(coverage * 100).toFixed(0)}% coverage`}
        </span>
        <button type="button" className="rounded-full border border-line p-2" aria-label="Keyboard shortcuts" onClick={() => setHelp((current) => !current)}>
          <HelpCircle size={16} />
        </button>
        <button type="button" className="rounded-full border border-line px-3 py-1.5 text-sm" onClick={() => setSection('evidence')}>
          How it works
        </button>
        <button type="button" className="rounded-full bg-gold px-3 py-1.5 text-sm font-semibold text-navy" onClick={() => setTourStep(0)}>
          Tour
        </button>
      </div>
      {help ? (
        <p className="px-4 pb-3 text-xs text-muted">
          Keys: 1 temperature, 2 rainfall, 3 humidity, Space plays the years, arrows step through years, Esc closes a region.
        </p>
      ) : null}
    </header>
  )
}
