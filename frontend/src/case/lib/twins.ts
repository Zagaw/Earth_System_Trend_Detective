import type { CaseFile, PlaceRecord, VariableId } from '../types'
import { VARIABLE_ORDER, isFiniteNumber } from './format'

export function suggestTwins(regions: PlaceRecord[]) {
  const rising = regions.filter(
    (region) => region.trend_status === 'significant_increasing' && isFiniteNumber(region.sen_slope),
  )
  const falling = regions.filter(
    (region) => region.trend_status === 'significant_decreasing' && isFiniteNumber(region.sen_slope),
  )
  let best: [PlaceRecord, PlaceRecord] | null = null
  let bestGap = Number.NEGATIVE_INFINITY
  for (const up of rising) {
    for (const down of falling) {
      const gap = (up.sen_slope ?? 0) - (down.sen_slope ?? 0)
      if (gap > bestGap) {
        bestGap = gap
        best = [up, down]
      }
    }
  }
  return best
}

export function isOpposite(left: PlaceRecord | undefined, right: PlaceRecord | undefined) {
  if (!left || !right) return false
  const statuses = new Set([left.trend_status, right.trend_status])
  return statuses.has('significant_increasing') && statuses.has('significant_decreasing')
}

export function oppositeRegionIds(file: CaseFile) {
  const ids = new Set<string>()
  for (const region of file.regions) {
    const statuses = VARIABLE_ORDER.map(
      (variable) => file.variables[variable].regions.find((item) => item.geography_id === region.id)?.trend_status,
    )
    if (statuses.includes('significant_increasing') && statuses.includes('significant_decreasing')) {
      ids.add(region.id)
    }
  }
  return ids
}

export function placeFor(file: CaseFile, variable: VariableId, regionId: string) {
  return file.variables[variable].regions.find((region) => region.geography_id === regionId)
}
