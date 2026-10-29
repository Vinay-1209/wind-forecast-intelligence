from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timezone

from app.config import Settings, assumption_note
from app.metrics import Metrics, calculate_metrics
from app.models import ActualRecord, ForecastRecord, IntervalResult
from app.normalize import ACTUAL_REVISION_RULE, DUPLICATE_FORECAST_RULE
from app.selection import analyse
from app.timeutil import format_z


@dataclass
class AnalysisService:
    settings: Settings
    actuals: tuple[ActualRecord, ...]
    forecasts: tuple[ForecastRecord, ...]
    fetched_at: str | None
    rejected: dict[str, int]

    def intervals(self, delivery_from: date, delivery_to: date) -> list[IntervalResult]:
        return analyse(
            list(self.actuals),
            list(self.forecasts),
            delivery_from,
            delivery_to,
            self.settings.timezone,
            self.settings.cutoff_hour,
            self.settings.cutoff_minute,
        )

    def summary(self, delivery_from: date, delivery_to: date) -> dict:
        intervals = self.intervals(delivery_from, delivery_to)
        metrics = calculate_metrics(intervals)
        quality = quality_counts(intervals)
        return {
            "delivery_from": delivery_from,
            "delivery_to": delivery_to,
            "rules": rules_payload(self.settings),
            "assumption_note": assumption_note(self.settings),
            **quality,
            "mae_mw": metrics.mae,
            "rmse_mw": metrics.rmse,
            "mbe_mw": metrics.mbe,
            "bias_label": metrics.bias_label,
            "largest_absolute_errors": largest_errors(intervals),
            "snapshot_fetched_at": self.fetched_at,
        }

    def timeseries(self, delivery_from: date, delivery_to: date) -> dict:
        return {
            "delivery_from": delivery_from,
            "delivery_to": delivery_to,
            "points": [series_point(interval) for interval in self.intervals(delivery_from, delivery_to)],
        }

    def forecast_details(self, start: datetime) -> IntervalResult | None:
        delivery_date = start.astimezone(self.settings.timezone).date()
        if delivery_date < self.settings.delivery_from or delivery_date > self.settings.delivery_to:
            return None
        target = start.astimezone(timezone.utc)
        for interval in self.intervals(delivery_date, delivery_date):
            if interval.start == target:
                return interval
        return None

    def data_quality(self, delivery_from: date, delivery_to: date) -> dict:
        intervals = self.intervals(delivery_from, delivery_to)
        quality = quality_counts(intervals)
        unexpected = [interval for interval in intervals if _unexpected(interval)]
        return {
            "delivery_from": delivery_from,
            "delivery_to": delivery_to,
            "rules": rules_payload(self.settings),
            "assumption_note": assumption_note(self.settings),
            **quality,
            "rejected_rows": self.rejected,
            "unexpected_gaps": [format_z(interval.start) for interval in unexpected[:100]],
            "unexpected_gaps_truncated": len(unexpected) > 100,
            "notes": _notes(self.settings, intervals),
            "snapshot_fetched_at": self.fetched_at,
        }


def rules_payload(settings: Settings) -> dict:
    return {
        "cutoff_time": settings.cutoff_label,
        "timezone": settings.timezone_name,
        "cutoff_inclusive": True,
        "alignment": "exact_start_time",
        "decision_from": settings.decision_from,
        "decision_to": settings.decision_to,
        "delivery_from": settings.delivery_from,
        "delivery_to": settings.delivery_to,
        "error_definition": "forecast_mw - actual_mw",
        "duplicate_forecast_rule": DUPLICATE_FORECAST_RULE,
        "actual_revision_rule": ACTUAL_REVISION_RULE,
    }


def quality_counts(intervals: list[IntervalResult]) -> dict:
    metrics = calculate_metrics(intervals)
    reasons = Counter(interval.reason for interval in intervals if interval.reason)
    hourly = [interval for interval in intervals if _utc_minute(interval) == 0]
    hourly_included = sum(interval.included for interval in hourly)
    return {
        "expected_intervals": len(intervals),
        "actuals_present": sum(interval.actual_mw is not None for interval in intervals),
        "included_pairs": metrics.pair_count,
        "excluded_by_reason": dict(reasons),
        "hourly_slots": len(hourly),
        "hourly_slots_included": hourly_included,
        "metrics_based_on_incomplete_hourly_coverage": hourly_included != len(hourly),
    }


def series_point(interval: IntervalResult) -> dict:
    absolute = None if interval.error_mw is None else abs(interval.error_mw)
    return {
        "start_time": format_z(interval.start),
        "actual_mw": interval.actual_mw,
        "forecast_mw": interval.forecast_mw,
        "error_mw": interval.error_mw,
        "absolute_error_mw": absolute,
        "included": interval.included,
        "reason": interval.reason,
        "publish_time": format_z(interval.publish_time) if interval.publish_time else None,
    }


def largest_errors(intervals: list[IntervalResult], limit: int = 5) -> list[dict]:
    included = [interval for interval in intervals if interval.included and interval.error_mw is not None]
    included.sort(key=lambda interval: (-abs(interval.error_mw), interval.start))
    return [series_point(interval) for interval in included[:limit]]


def detail_payload(interval: IntervalResult) -> dict:
    absolute = None if interval.error_mw is None else abs(interval.error_mw)
    return {
        "start_time": format_z(interval.start),
        "decision_date": interval.decision_date,
        "delivery_date": interval.delivery_date,
        "cutoff_time": format_z(interval.cutoff),
        "actual_mw": interval.actual_mw,
        "forecast_mw": interval.forecast_mw,
        "publish_time": format_z(interval.publish_time) if interval.publish_time else None,
        "error_mw": interval.error_mw,
        "absolute_error_mw": absolute,
        "included": interval.included,
        "reason": interval.reason,
        "versions": [
            {
                "publish_time": format_z(version.publish_time),
                "generation_mw": version.generation,
                "eligible": version.eligible,
                "selected": version.selected,
            }
            for version in interval.versions
        ],
    }


def _utc_minute(interval: IntervalResult) -> int:
    return interval.start.astimezone(timezone.utc).minute


def _unexpected(interval: IntervalResult) -> bool:
    if interval.included:
        return False
    # A :30 slot with no forecast is the known hourly-forecast alignment, not a data hole.
    if interval.reason == "no_forecast_for_interval" and _utc_minute(interval) == 30:
        return False
    return True


def _notes(settings: Settings, intervals: list[IntervalResult]) -> list[str]:
    half_hours = sum(
        1
        for interval in intervals
        if interval.reason == "no_forecast_for_interval" and _utc_minute(interval) == 30
    )
    notes = [
        assumption_note(settings),
        DUPLICATE_FORECAST_RULE,
        ACTUAL_REVISION_RULE,
    ]
    if half_hours:
        notes.append(
            f"{half_hours} half-hour actuals have no forecast at the same start time. "
            "They stay out of MAE, RMSE, and MBE, and they are not stored as zero error."
        )
    if any(_unexpected(interval) for interval in intervals):
        notes.append("Metrics use the included pairs only. Hourly coverage is incomplete.")
    return notes
