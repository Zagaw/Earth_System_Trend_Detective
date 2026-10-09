import { isFiniteNumber } from '../../lib/format'

export function Sparkline({ values, color }: { values: Array<number | null>; color: string }) {
  const finite = values.filter(isFiniteNumber)
  if (finite.length < 2) return <p className="text-xs text-muted">Not enough years for a sparkline.</p>
  const min = Math.min(...finite)
  const max = Math.max(...finite)
  const span = max - min || 1
  const width = 128
  const height = 36
  const step = width / Math.max(values.length - 1, 1)
  const segments: string[] = []
  let current = ''
  values.forEach((value, index) => {
    if (!isFiniteNumber(value)) {
      if (current) segments.push(current)
      current = ''
      return
    }
    const x = index * step
    const y = height - ((value - min) / span) * (height - 4) - 2
    current += `${current ? 'L' : 'M'}${x.toFixed(1)},${y.toFixed(1)}`
  })
  if (current) segments.push(current)
  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="h-9 w-32" aria-hidden="true">
      {segments.map((segment) => (
        <path key={segment} d={segment} fill="none" stroke={color} strokeWidth="2" />
      ))}
    </svg>
  )
}
