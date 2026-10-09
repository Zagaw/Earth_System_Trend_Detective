import type { MapMode, PlaceRecord, VariableId } from '../types'

export const VARIABLE_ORDER: VariableId[] = ['temperature', 'precipitation', 'relative_humidity']

export const VARIABLE_NAME: Record<VariableId, string> = {
  temperature: 'Temperature',
  precipitation: 'Rainfall',
  relative_humidity: 'Humidity',
}

export function isFiniteNumber(value: number | null | undefined): value is number {
  return value != null && Number.isFinite(value)
}

export function formatSigned(value: number, digits: number) {
  const rounded = Number(value.toFixed(digits))
  if (rounded === 0) return (0).toFixed(digits)
  const text = Math.abs(rounded).toFixed(digits)
  return rounded > 0 ? `+${text}` : `-${text}`
}

export function digitsFor(variable: VariableId, value: number | null) {
  if (!isFiniteNumber(value)) return 1
  if (variable === 'precipitation') return Math.abs(value) >= 100 ? 0 : 1
  if (variable === 'temperature') return 2
  return 1
}

export function unitShort(variable: VariableId) {
  if (variable === 'temperature') return '°C'
  if (variable === 'precipitation') return 'mm'
  return '%'
}

export function decadeUnit(variable: VariableId) {
  if (variable === 'temperature') return '°C per 10 years'
  if (variable === 'precipitation') return 'mm per 10 years'
  return 'pp per 10 years'
}

export function directionWords(variable: VariableId, slope: number | null) {
  if (!isFiniteNumber(slope) || slope === 0) return 'little estimated change'
  const rising = slope > 0
  if (variable === 'temperature') return rising ? 'warming' : 'cooling'
  if (variable === 'precipitation') return rising ? 'getting wetter' : 'getting drier'
  return rising ? 'more humid' : 'drier air'
}

export function decadePhrase(variable: VariableId, slopePerDecade: number | null) {
  if (!isFiniteNumber(slopePerDecade)) return 'unavailable'
  return `${formatSigned(slopePerDecade, digitsFor(variable, slopePerDecade))} ${decadeUnit(variable)}`
}

export function centroidLabel(variable: VariableId, slopePerDecade: number | null) {
  if (!isFiniteNumber(slopePerDecade)) return ''
  const digits = variable === 'temperature' ? 2 : digitsFor(variable, slopePerDecade)
  const suffix = variable === 'temperature' ? '°' : variable === 'relative_humidity' ? ' pp' : ''
  return `${formatSigned(slopePerDecade, digits)}${suffix}`
}

export function verdictLabel(status: string) {
  if (status === 'significant_increasing') return 'SIGNIFICANT INCREASE'
  if (status === 'significant_decreasing') return 'SIGNIFICANT DECREASE'
  if (status === 'not_significant') return 'NO CLEAR TREND'
  return 'NOT ENOUGH DATA'
}

export function verdictPlain(status: string) {
  if (status === 'significant_increasing') return 'Significant increase'
  if (status === 'significant_decreasing') return 'Significant decrease'
  if (status === 'not_significant') return 'No clear trend'
  return 'Not enough data'
}

export function metricValue(place: PlaceRecord, mode: MapMode, year: number) {
  if (mode === 'trend') return place.slope_per_decade
  if (mode === 'change') return place.absolute_difference
  return place.series.find((point) => point.year === year)?.anomaly ?? null
}

export function formatMeasure(value: number | null, digits: number, unit: string) {
  if (!isFiniteNumber(value)) return 'unavailable'
  return `${value.toFixed(digits)} ${unit}`
}
