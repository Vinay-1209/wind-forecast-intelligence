from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.models import ActualRecord, ForecastRecord, ForecastVersion, IntervalResult


def settlement_intervals(delivery_date: date, zone: ZoneInfo) -> list[datetime]:
    """48 half-hours beginning at local midnight on the Elexon settlement date."""
    local_midnight = datetime(
        delivery_date.year,
        delivery_date.month,
        delivery_date.day,
        tzinfo=zone,
    )
    start = local_midnight.astimezone(timezone.utc)
    return [start + timedelta(minutes=30 * period) for period in range(48)]


def decision_cutoff(
    delivery_date: date,
    zone: ZoneInfo,
    cutoff_hour: int,
    cutoff_minute: int,
) -> datetime:
    decision_date = delivery_date - timedelta(days=1)
    return datetime(
        decision_date.year,
        decision_date.month,
        decision_date.day,
        cutoff_hour,
        cutoff_minute,
        tzinfo=zone,
    )


def analyse(
    actuals: list[ActualRecord],
    forecasts: list[ForecastRecord],
    delivery_from: date,
    delivery_to: date,
    zone: ZoneInfo,
    cutoff_hour: int,
    cutoff_minute: int,
) -> list[IntervalResult]:
    actual_by_start = {record.start: record for record in actuals}
    forecasts_by_start: dict[datetime, list[ForecastRecord]] = defaultdict(list)
    for record in forecasts:
        forecasts_by_start[record.start].append(record)

    results: list[IntervalResult] = []
    delivery_date = delivery_from
    while delivery_date <= delivery_to:
        cutoff = decision_cutoff(delivery_date, zone, cutoff_hour, cutoff_minute)
        decision_date = delivery_date - timedelta(days=1)
        for start in settlement_intervals(delivery_date, zone):
            results.append(
                _evaluate_slot(
                    start=start,
                    decision_date=decision_date,
                    delivery_date=delivery_date,
                    cutoff=cutoff,
                    actual=actual_by_start.get(start),
                    forecasts=forecasts_by_start.get(start, []),
                )
            )
        delivery_date += timedelta(days=1)
    return results


def _evaluate_slot(
    start: datetime,
    decision_date: date,
    delivery_date: date,
    cutoff: datetime,
    actual: ActualRecord | None,
    forecasts: list[ForecastRecord],
) -> IntervalResult:
    ordered = sorted(forecasts, key=lambda record: (record.publish_time, record.generation))
    eligible = [record for record in ordered if record.publish_time <= cutoff]
    # A tied publication time keeps the lower generation, independent of input order.
    selected = (
        max(eligible, key=lambda record: (record.publish_time, -float(record.generation)))
        if eligible
        else None
    )
    chosen = (
        (selected.publish_time, selected.generation)
        if selected is not None and actual is not None
        else None
    )
    versions = tuple(
        ForecastVersion(
            publish_time=record.publish_time,
            generation=record.generation,
            eligible=record.publish_time <= cutoff,
            selected=(record.publish_time, record.generation) == chosen,
        )
        for record in ordered
    )

    if actual is None and not ordered:
        reason = "missing_interval"
    elif actual is None:
        reason = "no_actual"
    elif not ordered:
        reason = "no_forecast_for_interval"
    elif selected is None:
        reason = "no_eligible_forecast"
    else:
        reason = None

    included = reason is None and selected is not None and actual is not None
    forecast_mw = selected.generation if included else None
    actual_mw = actual.generation if actual is not None else None
    error_mw = None if not included else selected.generation - actual.generation
    return IntervalResult(
        start=start,
        decision_date=decision_date,
        delivery_date=delivery_date,
        cutoff=cutoff,
        actual_mw=actual_mw,
        forecast_mw=forecast_mw,
        publish_time=selected.publish_time if included else None,
        error_mw=error_mw,
        included=included,
        reason=reason,
        versions=versions,
    )
