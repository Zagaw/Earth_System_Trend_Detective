import { max } from 'd3-array'
import { scaleDiverging } from 'd3-scale'
import { interpolateBrBG, interpolateRdBu } from 'd3-scale-chromatic'
import type { VariableId } from '../types'
import { isFiniteNumber } from './format'

function mix(start: string, end: string, amount: number) {
  const read = (hex: string) => [0, 2, 4].map((index) => Number.parseInt(hex.slice(index, index + 2), 16))
  const from = read(start)
  const to = read(end)
  const channel = from.map((value, index) => Math.round(value + (to[index] - value) * amount))
  return `rgb(${channel[0]}, ${channel[1]}, ${channel[2]})`
}

function humidityInterpolator(amount: number) {
  if (amount <= 0.5) return mix('C2410C', 'F8FAFC', amount / 0.5)
  return mix('F8FAFC', '0F766E', (amount - 0.5) / 0.5)
}

function interpolatorFor(variable: VariableId) {
  if (variable === 'temperature') return (amount: number) => interpolateRdBu(1 - amount)
  if (variable === 'precipitation') return interpolateBrBG
  return humidityInterpolator
}

export function domainMax(values: Array<number | null | undefined>) {
  const span = max(values, (value) => (isFiniteNumber(value) ? Math.abs(value) : 0))
  return span ?? 0
}

export function paint(variable: VariableId, value: number | null | undefined, span: number) {
  if (!isFiniteNumber(value)) return '#334155'
  const limit = span > 0 ? span : 1
  const scale = scaleDiverging(interpolatorFor(variable)).domain([-limit, 0, limit])
  return scale(value)
}

export function legendStops(variable: VariableId, span: number, count = 24) {
  const limit = span > 0 ? span : 1
  return Array.from({ length: count }, (_, index) => {
    const value = -limit + (2 * limit * index) / (count - 1)
    return paint(variable, value, limit)
  })
}
