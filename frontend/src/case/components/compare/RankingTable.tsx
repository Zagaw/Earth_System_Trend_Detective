import { useMemo, useState } from 'react'
import { decadePhrase, isFiniteNumber, verdictPlain } from '../../lib/format'
import type { PlaceRecord, VariableId } from '../../types'

type Column = 'name' | 'slope' | 'status' | 'p' | 'baseline' | 'recent' | 'change'

function sortValue(row: PlaceRecord, column: Column) {
  if (column === 'name') return row.geography_name
  if (column === 'slope') return row.slope_per_decade
  if (column === 'status') return row.trend_status
  if (column === 'p') return row.adjusted_p_value
  if (column === 'baseline') return row.baseline_mean
  if (column === 'recent') return row.comparison_mean
  return row.absolute_difference
}

export function RankingTable({
  rows,
  variable,
  hoverId,
  onHover,
  onSelect,
}: {
  rows: PlaceRecord[]
  variable: VariableId
  hoverId: string | null
  onHover: (id: string | null) => void
  onSelect: (id: string) => void
}) {
  const [column, setColumn] = useState<Column>('slope')
  const [direction, setDirection] = useState<'asc' | 'desc'>('desc')
  const sorted = useMemo(() => {
    return [...rows].sort((left, right) => {
      const a = sortValue(left, column)
      const b = sortValue(right, column)
      if (typeof a === 'string' && typeof b === 'string') return direction === 'asc' ? a.localeCompare(b) : b.localeCompare(a)
      const an = isFiniteNumber(a as number | null) ? (a as number) : direction === 'asc' ? Number.POSITIVE_INFINITY : Number.NEGATIVE_INFINITY
      const bn = isFiniteNumber(b as number | null) ? (b as number) : direction === 'asc' ? Number.POSITIVE_INFINITY : Number.NEGATIVE_INFINITY
      return direction === 'asc' ? an - bn : bn - an
    })
  }, [rows, column, direction])

  const choose = (next: Column) => {
    if (next === column) setDirection((current) => (current === 'asc' ? 'desc' : 'asc'))
    else {
      setColumn(next)
      setDirection(next === 'name' ? 'asc' : 'desc')
    }
  }

  const header = (id: Column, label: string) => (
    <th className="px-2 py-2 text-left font-medium">
      <button type="button" onClick={() => choose(id)} className="text-muted">
        {label}
        {column === id ? (direction === 'asc' ? ' ↑' : ' ↓') : ''}
      </button>
    </th>
  )

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[720px] text-sm">
        <thead>
          <tr>
            {header('name', 'Region')}
            {header('slope', 'Per 10 years')}
            {header('status', 'Verdict')}
            {header('p', 'Corrected p')}
            {header('baseline', '2001–2010')}
            {header('recent', '2016–2025')}
            {header('change', 'Change')}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row) => (
            <tr
              key={row.geography_id}
              onMouseEnter={() => onHover(row.geography_id)}
              onMouseLeave={() => onHover(null)}
              onClick={() => onSelect(row.geography_id)}
              className={`cursor-pointer border-t border-line ${hoverId === row.geography_id ? 'bg-white/5' : ''} ${
                row.trend_status === 'insufficient_data'
                  ? 'text-[#64748B]'
                  : row.trend_status === 'not_significant'
                    ? 'bg-[repeating-linear-gradient(45deg,transparent_0_8px,rgba(148,163,184,0.08)_8px_9px)]'
                    : ''
              }`}
            >
              <td className="px-2 py-2">{row.geography_name}</td>
              <td className="tabular px-2 py-2">{decadePhrase(variable, row.slope_per_decade)}</td>
              <td className="px-2 py-2">{verdictPlain(row.trend_status)}</td>
              <td className="tabular px-2 py-2">{isFiniteNumber(row.adjusted_p_value) ? row.adjusted_p_value.toFixed(4) : ''}</td>
              <td className="tabular px-2 py-2">{isFiniteNumber(row.baseline_mean) ? row.baseline_mean.toFixed(1) : ''}</td>
              <td className="tabular px-2 py-2">{isFiniteNumber(row.comparison_mean) ? row.comparison_mean.toFixed(1) : ''}</td>
              <td className="tabular px-2 py-2">{isFiniteNumber(row.absolute_difference) ? row.absolute_difference.toFixed(1) : ''}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
