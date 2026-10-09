import { useEffect, useId, useMemo, useRef, useState } from 'react'
import { featureCentroid, makeProjection } from '../../lib/geo'
import { domainMax, paint } from '../../lib/colors'
import { centroidLabel, metricValue } from '../../lib/format'
import type { BoundaryCollection, MapMode, PlaceRecord, VariableId } from '../../types'

export function MyanmarMap({
  boundaries,
  places,
  variable,
  mode,
  year,
  selectedId,
  hoverId,
  highlightIds,
  goldIds,
  marks = [],
  showLabels = true,
  showRaindrops = false,
  onHover,
  onSelect,
}: {
  boundaries: BoundaryCollection
  places: PlaceRecord[]
  variable: VariableId
  mode: MapMode
  year: number
  selectedId?: string | null
  hoverId?: string | null
  highlightIds?: string[]
  goldIds?: Set<string>
  marks?: Array<{ id: string; color: string }>
  showLabels?: boolean
  showRaindrops?: boolean
  onHover?: (id: string | null) => void
  onSelect?: (id: string) => void
}) {
  const uid = useId().replaceAll(':', '')
  const frame = useRef<HTMLDivElement>(null)
  const [size, setSize] = useState({ width: 640, height: 560 })
  const byId = useMemo(() => new Map(places.map((place) => [place.geography_id, place])), [places])
  const span = domainMax(places.map((place) => metricValue(place, mode, year)))
  const rainMax = Math.max(...places.map((place) => place.comparison_mean ?? 0), 1)

  useEffect(() => {
    const element = frame.current
    if (!element) return
    const observer = new ResizeObserver(() => {
      setSize({ width: element.clientWidth, height: element.clientHeight })
    })
    observer.observe(element)
    setSize({ width: element.clientWidth, height: element.clientHeight })
    return () => observer.disconnect()
  }, [])

  const drawing = useMemo(() => {
    if (size.width < 40 || size.height < 40) return null
    return makeProjection(boundaries, size.width, size.height)
  }, [boundaries, size])

  return (
    <div ref={frame} className="h-full min-h-[420px] w-full">
      {drawing ? (
        <svg viewBox={`0 0 ${size.width} ${size.height}`} className="h-full w-full" role="img" aria-label="Myanmar regions">
          <defs>
            <pattern id={`hatch-${uid}`} patternUnits="userSpaceOnUse" width="7" height="7" patternTransform="rotate(45)">
              <line x1="0" y1="0" x2="0" y2="7" stroke="rgba(248,250,252,0.7)" strokeWidth="1.4" />
            </pattern>
            <filter id={`glow-${uid}`}>
              <feDropShadow dx="0" dy="0" stdDeviation="3" floodColor="#FBBF24" floodOpacity="0.85" />
            </filter>
          </defs>
          {boundaries.features.map((feature) => {
            const place = byId.get(feature.properties.id)
            const status = place?.trend_status ?? 'insufficient_data'
            const value = place ? metricValue(place, mode, year) : null
            const missing = !place || status === 'insufficient_data' || value == null
            const significant = status.startsWith('significant')
            const geometry = drawing.path(feature)
            if (!geometry) return null
            const mark = marks.find((item) => item.id === feature.properties.id)
            const highlighted = highlightIds?.includes(feature.properties.id) || goldIds?.has(feature.properties.id)
            const selected = selectedId === feature.properties.id
            const hovered = hoverId === feature.properties.id
            const stroke = selected || highlighted ? '#FBBF24' : mark ? mark.color : hovered ? '#F8FAFC' : significant ? '#F8FAFC' : '#64748B'
            const [cx, cy] = featureCentroid(feature, drawing.projection)
            const drop = place?.comparison_mean
            const dropRadius = drop == null ? 0 : 3 + (drop / rainMax) * 8
            return (
              <g key={feature.properties.id}>
                <path
                  d={geometry}
                  fill={missing ? '#334155' : paint(variable, value, span)}
                  fillOpacity={missing ? 1 : significant ? 0.95 : 0.35}
                  stroke={stroke}
                  strokeWidth={selected || highlighted || mark ? 2.4 : significant ? 1.5 : 1}
                  strokeDasharray={missing ? '3 3' : undefined}
                  filter={hovered ? `url(#glow-${uid})` : undefined}
                  className="cursor-pointer transition-[fill] duration-300"
                  onMouseEnter={() => onHover?.(feature.properties.id)}
                  onMouseLeave={() => onHover?.(null)}
                  onClick={() => onSelect?.(feature.properties.id)}
                />
                {!missing && !significant ? (
                  <path d={geometry} fill={`url(#hatch-${uid})`} pointerEvents="none" />
                ) : null}
                {showRaindrops && variable === 'precipitation' && drop != null && Number.isFinite(cx) ? (
                  <circle cx={cx} cy={cy} r={dropRadius} fill="#7DD3FC" fillOpacity="0.85" stroke="#F8FAFC" strokeWidth="0.6" pointerEvents="none" />
                ) : null}
                {showLabels && significant && place && Number.isFinite(cx) ? (
                  <text x={cx} y={cy} textAnchor="middle" dominantBaseline="middle" fill="#F8FAFC" fontSize="11" fontWeight="600" pointerEvents="none">
                    {centroidLabel(variable, place.slope_per_decade)}
                  </text>
                ) : null}
              </g>
            )
          })}
          {mode === 'year' ? (
            <text x={size.width - 18} y={size.height - 16} textAnchor="end" fill="rgba(248,250,252,0.2)" fontSize="64" fontFamily="Poppins, sans-serif">
              {year}
            </text>
          ) : null}
        </svg>
      ) : null}
    </div>
  )
}
