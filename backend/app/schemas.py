from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class RulesResponse(BaseModel):
    cutoff_time: str
    timezone: str
    cutoff_inclusive: bool
    alignment: str
    decision_from: date
    decision_to: date
    delivery_from: date
    delivery_to: date
    error_definition: str
    duplicate_forecast_rule: str
    actual_revision_rule: str


class SeriesPoint(BaseModel):
    start_time: str
    actual_mw: int | float | None
    forecast_mw: int | float | None
    error_mw: int | float | None
    absolute_error_mw: int | float | None
    included: bool
    reason: str | None
    publish_time: str | None


class SummaryResponse(BaseModel):
    delivery_from: date
    delivery_to: date
    rules: RulesResponse
    assumption_note: str
    expected_intervals: int
    actuals_present: int
    included_pairs: int
    excluded_by_reason: dict[str, int]
    hourly_slots: int
    hourly_slots_included: int
    metrics_based_on_incomplete_hourly_coverage: bool
    mae_mw: float | None
    rmse_mw: float | None
    mbe_mw: float | None
    bias_label: str | None
    largest_absolute_errors: list[SeriesPoint]
    snapshot_fetched_at: str | None


class TimeseriesResponse(BaseModel):
    delivery_from: date
    delivery_to: date
    points: list[SeriesPoint]


class ForecastVersionResponse(BaseModel):
    publish_time: str
    generation_mw: int | float
    eligible: bool
    selected: bool


class ForecastDetailsResponse(BaseModel):
    start_time: str
    decision_date: date
    delivery_date: date
    cutoff_time: str
    actual_mw: int | float | None
    forecast_mw: int | float | None
    publish_time: str | None
    error_mw: int | float | None
    absolute_error_mw: int | float | None
    included: bool
    reason: str | None
    versions: list[ForecastVersionResponse]


class DataQualityResponse(BaseModel):
    delivery_from: date
    delivery_to: date
    rules: RulesResponse
    assumption_note: str
    expected_intervals: int
    actuals_present: int
    included_pairs: int
    excluded_by_reason: dict[str, int]
    hourly_slots: int
    hourly_slots_included: int
    metrics_based_on_incomplete_hourly_coverage: bool
    rejected_rows: dict[str, int]
    unexpected_gaps: list[str]
    unexpected_gaps_truncated: bool
    notes: list[str]
    snapshot_fetched_at: str | None


class HealthResponse(BaseModel):
    status: str
    snapshot_fetched_at: str | None = None
    actual_rows: int = 0
    forecast_rows: int = 0
    delivery_from: date | None = None
    delivery_to: date | None = None
    cutoff_time: str | None = None
    timezone: str | None = None
