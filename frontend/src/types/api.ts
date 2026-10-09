export type VariableId = 'precipitation' | 'temperature' | 'relative_humidity'

export interface VariableInfo {
  id: VariableId
  label: string
  source_parameter: string
  source_unit: string
  long_name: string
  temporal_meaning: string
  analysis_unit: string
  aggregation_rule: string
  slope_unit: string
  conversion: string | null
  verified: boolean
  verified_on: string
}

export interface MetadataResponse {
  project: string
  geography: string
  community: string
  requested_period: {
    start_year: number
    end_year: number
  }
  study_grid_status: 'not_ingested' | 'ready'
  fill_value: number
  month_key_policy: string
  regional_minimum_span_degrees: number
  grid_note: string
  variables: VariableInfo[]
  incomplete: string[]
}

export interface SeriesPoint {
  year: number
  month: number | null
  value: number | null
  coverage_fraction: number | null
}

export interface TimeSeriesResponse {
  variable: VariableId
  variable_label: string
  unit: string
  region_id: string
  region_name: string
  aggregation: string
  season: string | null
  data: SeriesPoint[]
  trend_line: Array<{ year: number; value: number }>
}

export interface TrendResult {
  variable: VariableId
  variable_label: string
  unit: string
  slope_unit: string
  geography_id: string
  geography_name: string
  sen_slope: number | null
  slope_text: string
  p_value: number | null
  adjusted_p_value: number | null
  confidence_interval_95: [number, number] | null
  trend_status: string
  trend_direction: string
  valid_years: number
  expected_years: number
  coverage_fraction: number | null
  interpretation: string
  test_method: string
  autocorrelation_method: string
  multiple_testing_method: string
  effective_start_year: number | null
  effective_end_year: number | null
  aggregation_label: string
}

export interface RegionRecord {
  id: string
  name: string
  level: string
  iso: string
  cell_count: number
}

export interface GridFeature {
  type: 'Feature'
  geometry: { type: 'Polygon'; coordinates: number[][][] }
  properties: {
    latitude: number
    longitude: number
    region_name: string | null
    sen_slope: number | null
    p_value: number | null
    adjusted_p_value: number | null
    trend_status: string
    valid_years: number
    coverage_fraction: number | null
    slope_unit: string
    test_method: string
  }
}

export interface ImpactSummary {
  variable_label: string
  unit: string
  geography_name: string
  baseline_start_year: number
  baseline_end_year: number
  comparison_start_year: number
  comparison_end_year: number
  baseline_mean: number | null
  comparison_mean: number | null
  absolute_difference: number | null
  relative_difference_percent: number | null
  significant_increasing_cells: number
  significant_decreasing_cells: number
  increasing_area_fraction: number | null
  decreasing_area_fraction: number | null
  tested_cell_count: number
  years_above_baseline_p90: number | null
  years_below_baseline_p10: number | null
  interpretation: string
  limitation: string
}

export interface AnalysisConfigResponse {
  significance_alpha: number
  trend_method: string
  significance_test: string
  multiple_testing: string
  minimum_valid_years: number
  minimum_valid_months_for_means: number
  minimum_valid_months_for_rainfall_total: number
  seasons_planned: string[]
  calculations_implemented: boolean
  note: string
}
