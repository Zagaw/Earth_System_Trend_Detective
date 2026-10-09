export type VariableId = 'temperature' | 'precipitation' | 'relative_humidity'
export type SectionId = 'overview' | 'map' | 'fingerprint' | 'compare' | 'evidence'
export type MapMode = 'trend' | 'year' | 'change'

export interface SeriesPoint {
  year: number
  value: number | null
  anomaly: number | null
}

export interface PlaceRecord {
  geography_id: string
  geography_name: string
  iso: string | null
  level: string
  sen_slope: number | null
  slope_per_decade: number | null
  slope_text: string
  slope_unit: string
  p_value: number | null
  adjusted_p_value: number | null
  confidence_interval_95: [number | null, number | null] | null
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
  baseline_mean: number | null
  comparison_mean: number | null
  absolute_difference: number | null
  relative_difference_percent: number | null
  series: SeriesPoint[]
  trend_line: Array<{ year: number; value: number }>
}

export interface VariableCase {
  id: VariableId
  label: string
  unit: string
  slope_unit: string
  decade_unit: string
  source_parameter: string
  source_unit: string
  temporal_meaning: string
  aggregation_rule: string
  conversion: string | null
  national: PlaceRecord
  regions: PlaceRecord[]
}

export interface CaseFile {
  is_sample: boolean
  project: string
  source: string
  community: string
  anomaly_reference: string
  start_year: number
  end_year: number
  baseline_start_year: number
  baseline_end_year: number
  comparison_start_year: number
  comparison_end_year: number
  significance_alpha: number
  national: { id: string; name: string; iso: string; level: string }
  regions: Array<{ id: string; name: string; iso: string; level: string; cell_count: number }>
  variables: Record<VariableId, VariableCase>
  evidence: {
    mask_policy: string
    boundary_overlap_cells: number
    unassigned_interior_cells: number
    masked_cell_count: number
    minimum_valid_years: number
    minimum_spatial_coverage: number
    spatial_weighting: string
    trend_method: string
    significance_test: string
    multiple_testing_regions: string
    multiple_testing_national: string
    retrieved_at: string
    limitations: string[]
  }
}

export interface BoundaryCollection {
  type: 'FeatureCollection'
  features: Array<{
    type: 'Feature'
    properties: { id: string; name: string; iso: string }
    geometry: GeoJSON.Geometry
  }>
}
