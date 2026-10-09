import { useSearchParams } from 'react-router-dom'
import type { VariableId } from '../types/api'

const variables: VariableId[] = ['temperature', 'precipitation', 'relative_humidity']

export function useAnalysisQuery() {
  const [params, setParams] = useSearchParams()
  const variable = asVariable(params.get('variable'))
  const startYear = numberOr(params.get('start'), 2001)
  const endYear = numberOr(params.get('end'), 2025)
  const aggregation = params.get('aggregation') === 'seasonal' ? 'seasonal' : 'annual'
  const season = params.get('season') || 'JJA'
  const regionId = params.get('region') || ''

  function update(key: string, value: string) {
    const next = new URLSearchParams(params)
    if (value) next.set(key, value)
    else next.delete(key)
    setParams(next)
  }

  const query = new URLSearchParams({
    variable,
    start_year: String(startYear),
    end_year: String(endYear),
    aggregation,
  })
  if (regionId) query.set('region_id', regionId)
  if (aggregation === 'seasonal') query.set('season', season)

  return {
    variable,
    startYear,
    endYear,
    aggregation,
    season,
    regionId,
    update,
    queryString: query.toString(),
  }
}

export function queryForVariable(queryString: string, variable: VariableId) {
  const params = new URLSearchParams(queryString)
  params.set('variable', variable)
  return params.toString()
}

function asVariable(value: string | null): VariableId {
  if (value === 'precipitation' || value === 'relative_humidity' || value === 'temperature') {
    return value
  }
  return 'temperature'
}

function numberOr(value: string | null, fallback: number) {
  if (value == null || value.trim() === '') return fallback
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

export { variables }
