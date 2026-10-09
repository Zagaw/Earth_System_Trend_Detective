import type { CaseFile, PlaceRecord, VariableId } from '../types'
import { isFiniteNumber } from './format'

function cell(value: number | null) {
  return isFiniteNumber(value) ? String(value) : ''
}

function quote(value: string) {
  return `"${value.replaceAll('"', '""')}"`
}

export function rankingCsv(file: CaseFile, variable: VariableId, rows: PlaceRecord[]) {
  const definition = file.variables[variable]
  const header = [
    'region',
    'iso',
    'slope_per_year',
    'slope_unit',
    'slope_per_decade',
    'decade_unit',
    'trend_status',
    'adjusted_p_value',
    'baseline_mean',
    'comparison_mean',
    'absolute_difference',
    'unit',
  ]
  const lines = rows.map((row) =>
    [
      quote(row.geography_name),
      row.iso ?? '',
      cell(row.sen_slope),
      definition.slope_unit,
      cell(row.slope_per_decade),
      definition.decade_unit,
      row.trend_status,
      cell(row.adjusted_p_value),
      cell(row.baseline_mean),
      cell(row.comparison_mean),
      cell(row.absolute_difference),
      definition.unit,
    ].join(','),
  )
  if (file.is_sample) lines.unshift('SAMPLE DATA - NOT REAL NASA RESULTS')
  return [header.join(','), ...lines].join('\n')
}

export function downloadText(filename: string, contents: string) {
  const blob = new Blob([contents], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}
