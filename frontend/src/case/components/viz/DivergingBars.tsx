import { domainMax, paint } from '../../lib/colors'
import { decadePhrase, verdictPlain } from '../../lib/format'
import type { VariableId } from '../../types'

export interface BarItem {
  id: string
  name: string
  value: number | null
  status: string
}

export function DivergingBars({
  items,
  variable,
  hoverId,
  onHover,
  onSelect,
  hatch,
  caption,
}: {
  items: BarItem[]
  variable: VariableId
  hoverId: string | null
  onHover: (id: string | null) => void
  onSelect: (id: string) => void
  hatch: boolean
  caption?: (item: BarItem) => string
}) {
  const span = domainMax(items.map((item) => item.value))
  const limit = span > 0 ? span : 1
  return (
    <div className="max-h-[420px] space-y-1 overflow-y-auto pr-1">
      {items.map((item) => {
        const width = item.value == null ? 0 : (Math.abs(item.value) / limit) * 50
        const color = paint(variable, item.value, span)
        const missing = item.status === 'insufficient_data' || item.value == null
        return (
          <button
            key={item.id}
            type="button"
            className={`grid w-full grid-cols-[88px_1fr] items-center gap-2 rounded-lg px-1 py-1 text-left ${
              hoverId === item.id ? 'bg-white/5' : ''
            }`}
            onMouseEnter={() => onHover(item.id)}
            onMouseLeave={() => onHover(null)}
            onClick={() => onSelect(item.id)}
            title={caption ? caption(item) : `${item.name}: ${decadePhrase(variable, item.value)}. ${verdictPlain(item.status)}`}
          >
            <span className="truncate text-xs text-muted">{item.name}</span>
            <span className="relative h-3">
              <span className="absolute inset-y-0 left-1/2 w-px bg-line" />
              <span
                className="absolute top-0 h-3 rounded-sm"
                style={{
                  width: `${width}%`,
                  left: item.value != null && item.value < 0 ? `${50 - width}%` : '50%',
                  background: missing
                    ? '#334155'
                    : hatch && item.status === 'not_significant'
                      ? `repeating-linear-gradient(45deg, ${color} 0 3px, transparent 3px 6px)`
                      : color,
                  opacity: item.status === 'not_significant' ? 0.7 : 1,
                }}
              />
            </span>
          </button>
        )
      })}
    </div>
  )
}
