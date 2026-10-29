export const STUDY_FROM = "2026-01-02"
export const STUDY_TO = "2026-02-01"

export interface DateRange {
  from: string
  to: string
}

export interface Rules {
  cutoff_time: string
  timezone: string
  cutoff_inclusive: boolean
  alignment: string
  decision_from: string
  decision_to: string
  delivery_from: string
  delivery_to: string
  error_definition: string
  duplicate_forecast_rule: string
  actual_revision_rule: string
}

export interface SeriesPoint {
  start_time: string
  actual_mw: number | null
  forecast_mw: number | null
  error_mw: number | null
  absolute_error_mw: number | null
  included: boolean
  reason: string | null
  publish_time: string | null
}

export interface Summary {
  delivery_from: string
  delivery_to: string
  rules: Rules
  assumption_note: string
  expected_intervals: number
  actuals_present: number
  included_pairs: number
  excluded_by_reason: Record<string, number>
  hourly_slots: number
  hourly_slots_included: number
  metrics_based_on_incomplete_hourly_coverage: boolean
  mae_mw: number | null
  rmse_mw: number | null
  mbe_mw: number | null
  bias_label: string | null
  largest_absolute_errors: SeriesPoint[]
  snapshot_fetched_at: string | null
}

export interface Timeseries {
  delivery_from: string
  delivery_to: string
  points: SeriesPoint[]
}

export interface ForecastVersion {
  publish_time: string
  generation_mw: number
  eligible: boolean
  selected: boolean
}

export interface ForecastDetails {
  start_time: string
  decision_date: string
  delivery_date: string
  cutoff_time: string
  actual_mw: number | null
  forecast_mw: number | null
  publish_time: string | null
  error_mw: number | null
  absolute_error_mw: number | null
  included: boolean
  reason: string | null
  versions: ForecastVersion[]
}

export interface DataQuality {
  delivery_from: string
  delivery_to: string
  rules: Rules
  assumption_note: string
  expected_intervals: number
  actuals_present: number
  included_pairs: number
  excluded_by_reason: Record<string, number>
  hourly_slots: number
  hourly_slots_included: number
  metrics_based_on_incomplete_hourly_coverage: boolean
  rejected_rows: Record<string, number>
  unexpected_gaps: string[]
  unexpected_gaps_truncated: boolean
  notes: string[]
  snapshot_fetched_at: string | null
}
