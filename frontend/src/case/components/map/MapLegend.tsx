import { legendStops } from '../../lib/colors'
import { digitsFor, formatSigned } from '../../lib/format'
import type { MapMode, VariableId } from '../../types'

export function MapLegend({
  variable,
  mode,
  span,
  unit,
  reference,
}: {
  variable: VariableId
  mode: MapMode
  span: number
  unit: string
  reference: string
}) {
  const stops = legendStops(variable, span)
  const limit = span > 0 ? span : 0
  const digits = digitsFor(variable, limit)
  const title = mode === 'trend' ? 'Change per 10 years' : mode === 'change' ? 'Change between decades' : reference
  return (
    <div data-tour="legend" className="mt-3 grid gap-3 rounded-2xl border border-line bg-surface p-3 md:grid-cols-[1.4fr_1fr]">
      <div>
        <p className="text-xs tracking-wide text-muted uppercase">{title}</p>
        <div className="mt-2 h-3 rounded-full" style={{ background: `linear-gradient(90deg, ${stops.join(',')})` }} />
        <div className="tabular mt-1 flex justify-between text-xs text-muted">
          <span>{formatSigned(-limit, digits)}</span>
          <span>0</span>
          <span>{formatSigned(limit, digits)}</span>
        </div>
        <p className="mt-1 text-xs text-muted">{unit}</p>
      </div>
      <ul className="space-y-1 text-xs text-muted">
        <li className="flex items-center gap-2">
          <span className="h-3 w-5 rounded-sm border border-white bg-white/80" /> Solid means a significant trend
        </li>
        <li className="flex items-center gap-2">
          <span className="h-3 w-5 rounded-sm border border-white/40 bg-[repeating-linear-gradient(45deg,#94A3B8_0_2px,transparent_2px_4px)]" />
          Hatched means no clear change
        </li>
        <li className="flex items-center gap-2">
          <span className="h-3 w-5 rounded-sm border border-dashed border-[#64748B] bg-[#334155]" /> Grey means not enough data
        </li>
      </ul>
    </div>
  )
}
