import type { DataQuality, ForecastDetails, SeriesPoint, Summary, Timeseries } from "../api/types.ts"

const rules = {
  cutoff_time: "09:50",
  timezone: "Europe/London",
  cutoff_inclusive: true,
  alignment: "exact_start_time",
  decision_from: "2026-01-01",
  decision_to: "2026-01-31",
  delivery_from: "2026-01-02",
  delivery_to: "2026-02-01",
  error_definition: "forecast_mw - actual_mw",
  duplicate_forecast_rule: "Tied publication times keep the lower generation.",
  actual_revision_rule: "A later actual publication replaces an earlier one.",
}

export const matchedPoint: SeriesPoint = {
  start_time: "2026-01-11T10:00:00Z",
  actual_mw: 14789,
  forecast_mw: 18883,
  error_mw: 4094,
  absolute_error_mw: 4094,
  included: true,
  reason: null,
  publish_time: "2026-01-10T09:30:00Z",
}

export const halfHourPoint: SeriesPoint = {
  start_time: "2026-01-11T10:30:00Z",
  actual_mw: 14000,
  forecast_mw: null,
  error_mw: null,
  absolute_error_mw: null,
  included: false,
  reason: "no_forecast_for_interval",
  publish_time: null,
}

export const summary: Summary = {
  delivery_from: "2026-01-02",
  delivery_to: "2026-02-01",
  rules,
  assumption_note: "A forecast is eligible at or before 09:50 Europe/London on the day before delivery.",
  expected_intervals: 1488,
  actuals_present: 1488,
  included_pairs: 744,
  excluded_by_reason: { no_forecast_for_interval: 744 },
  hourly_slots: 744,
  hourly_slots_included: 744,
  metrics_based_on_incomplete_hourly_coverage: false,
  mae_mw: 1995.6,
  rmse_mw: 2498.8,
  mbe_mw: 1728,
  bias_label: "overforecast",
  largest_absolute_errors: [matchedPoint],
  snapshot_fetched_at: "2026-10-28T17:35:49Z",
}

export const series: Timeseries = {
  delivery_from: "2026-01-02",
  delivery_to: "2026-02-01",
  points: [matchedPoint, halfHourPoint],
}

export const quality: DataQuality = {
  ...summary,
  rejected_rows: {},
  unexpected_gaps: [],
  unexpected_gaps_truncated: false,
  notes: [
    summary.assumption_note,
    "1 half-hour actual has no forecast at the same start time. It stays out of the metrics and is not stored as zero error.",
  ],
}

export const details: ForecastDetails = {
  start_time: matchedPoint.start_time,
  decision_date: "2026-01-10",
  delivery_date: "2026-01-11",
  cutoff_time: "2026-01-10T09:50:00Z",
  actual_mw: 14789,
  forecast_mw: 18883,
  publish_time: "2026-01-10T09:30:00Z",
  error_mw: 4094,
  absolute_error_mw: 4094,
  included: true,
  reason: null,
  versions: [
    {
      publish_time: "2026-01-10T09:30:00Z",
      generation_mw: 18883,
      eligible: true,
      selected: true,
    },
    {
      publish_time: "2026-01-10T11:30:00Z",
      generation_mw: 18835,
      eligible: false,
      selected: false,
    },
  ],
}

export const excludedDetails: ForecastDetails = {
  start_time: halfHourPoint.start_time,
  decision_date: "2026-01-10",
  delivery_date: "2026-01-11",
  cutoff_time: "2026-01-10T09:50:00Z",
  actual_mw: 14000,
  forecast_mw: null,
  publish_time: null,
  error_mw: null,
  absolute_error_mw: null,
  included: false,
  reason: "no_forecast_for_interval",
  versions: [],
}
