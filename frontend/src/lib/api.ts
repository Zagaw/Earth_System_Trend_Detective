import { z } from 'zod'
import type {
  AnalysisConfigResponse,
  GridFeature,
  ImpactSummary,
  MetadataResponse,
  RegionRecord,
  TimeSeriesResponse,
  TrendResult,
} from '../types/api'

export const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export class ApiRequestError extends Error {
  status: number
  code: string

  constructor(status: number, code: string, message: string) {
    super(message)
    this.status = status
    this.code = code
  }
}

const variableSchema = z.object({
  id: z.enum(['precipitation', 'temperature', 'relative_humidity']),
  label: z.string(),
  source_parameter: z.string(),
  source_unit: z.string(),
  long_name: z.string(),
  temporal_meaning: z.string(),
  analysis_unit: z.string(),
  aggregation_rule: z.string(),
  slope_unit: z.string(),
  conversion: z.string().nullable(),
  verified: z.boolean(),
  verified_on: z.string(),
})

const metadataSchema = z.object({
  project: z.string(),
  geography: z.string(),
  community: z.string(),
  requested_period: z.object({
    start_year: z.number(),
    end_year: z.number(),
  }),
  study_grid_status: z.enum(['not_ingested', 'ready']),
  fill_value: z.number(),
  month_key_policy: z.string(),
  regional_minimum_span_degrees: z.number(),
  grid_note: z.string(),
  variables: z.array(variableSchema),
  incomplete: z.array(z.string()),
})

const analysisConfigSchema = z.object({
  significance_alpha: z.number(),
  trend_method: z.string(),
  significance_test: z.string(),
  multiple_testing: z.string(),
  minimum_valid_years: z.number(),
  minimum_valid_months_for_means: z.number(),
  minimum_valid_months_for_rainfall_total: z.number(),
  seasons_planned: z.array(z.string()),
  calculations_implemented: z.boolean(),
  note: z.string(),
})

export async function getJson(path: string): Promise<unknown> {
  const response = await fetch(`${API_BASE}${path}`)
  const body: unknown = await response.json().catch(() => null)
  if (!response.ok) {
    const record = body && typeof body === 'object' ? (body as Record<string, unknown>) : {}
    const message = typeof record.message === 'string' ? record.message : response.statusText
    const code = typeof record.error === 'string' ? record.error : 'request_failed'
    throw new ApiRequestError(response.status, code, message)
  }
  return body
}

export async function getMetadata(): Promise<MetadataResponse> {
  return metadataSchema.parse(await getJson('/metadata'))
}

export async function getAnalysisConfig(): Promise<AnalysisConfigResponse> {
  return analysisConfigSchema.parse(await getJson('/analysis/config'))
}

export function getTimeSeries(query: string): Promise<TimeSeriesResponse> {
  return getJson(`/climate/timeseries?${query}`) as Promise<TimeSeriesResponse>
}

export function getTrend(query: string): Promise<TrendResult> {
  return getJson(`/trends/summary?${query}`) as Promise<TrendResult>
}

export function getRegions(): Promise<{ regions: RegionRecord[] }> {
  return getJson('/regions') as Promise<{ regions: RegionRecord[] }>
}

export function getGrid(query: string): Promise<{ features: GridFeature[] }> {
  return getJson(`/trends/grid?${query}`) as Promise<{ features: GridFeature[] }>
}

export function getComparison(query: string): Promise<{ regions: TrendResult[] }> {
  return getJson(`/compare?${query}`) as Promise<{ regions: TrendResult[] }>
}

export function getImpact(query: string): Promise<ImpactSummary> {
  return getJson(`/impact/summary?${query}`) as Promise<ImpactSummary>
}

export function getAnomalies(query: string): Promise<{ data: Array<{ year: number; anomaly: number | null }> }> {
  return getJson(`/impact/anomalies?${query}`) as Promise<{
    data: Array<{ year: number; anomaly: number | null }>
  }>
}
