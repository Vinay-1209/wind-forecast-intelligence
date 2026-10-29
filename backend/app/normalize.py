from __future__ import annotations

import math
from datetime import date

from app.models import ActualRecord, ForecastRecord
from app.timeutil import parse_timestamp

DUPLICATE_FORECAST_RULE = (
    "If two forecast rows share a delivery start and publication time but disagree on generation, "
    "the lower generation is kept so the result does not depend on response order."
)
ACTUAL_REVISION_RULE = (
    "If two actual rows share a delivery start, the later publication time is kept. "
    "If those publication times also match and the generation values disagree, the lower generation is kept."
)


def parse_generation(value: object) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("generation must be a number")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("generation must be finite")
    return value


def normalise_actuals(rows: list[dict]) -> tuple[list[ActualRecord], dict[str, int]]:
    rejected = {"other_fuel": 0, "invalid_actual": 0, "duplicate_actual_conflict": 0}
    kept: dict[object, ActualRecord] = {}
    for row in rows:
        if row.get("fuelType") != "WIND":
            rejected["other_fuel"] += 1
            continue
        try:
            record = ActualRecord(
                start=parse_timestamp(row.get("startTime")),
                generation=parse_generation(row.get("generation")),
                settlement_date=_settlement_date(row.get("settlementDate")),
                settlement_period=_settlement_period(row.get("settlementPeriod")),
                publish_time=_optional_time(row.get("publishTime")),
            )
        except (TypeError, ValueError):
            rejected["invalid_actual"] += 1
            continue
        current = kept.get(record.start)
        if current is None:
            kept[record.start] = record
            continue
        if current.generation != record.generation or current.publish_time != record.publish_time:
            rejected["duplicate_actual_conflict"] += 1
        kept[record.start] = _prefer_actual(current, record)
    return list(kept.values()), rejected


def normalise_forecasts(rows: list[dict]) -> tuple[list[ForecastRecord], dict[str, int]]:
    rejected = {"invalid_forecast": 0, "duplicate_forecast_conflict": 0}
    kept: dict[tuple, ForecastRecord] = {}
    for row in rows:
        try:
            record = ForecastRecord(
                start=parse_timestamp(row.get("startTime")),
                publish_time=parse_timestamp(row.get("publishTime")),
                generation=parse_generation(row.get("generation")),
            )
        except (TypeError, ValueError):
            rejected["invalid_forecast"] += 1
            continue
        key = (record.start, record.publish_time)
        current = kept.get(key)
        if current is None:
            kept[key] = record
            continue
        if current.generation != record.generation:
            rejected["duplicate_forecast_conflict"] += 1
            if record.generation < current.generation:
                kept[key] = record
    return list(kept.values()), rejected


def _prefer_actual(current: ActualRecord, incoming: ActualRecord) -> ActualRecord:
    current_published = current.publish_time
    incoming_published = incoming.publish_time
    if current_published != incoming_published:
        if incoming_published is None:
            return current
        if current_published is None or incoming_published > current_published:
            return incoming
        return current
    if incoming.generation < current.generation:
        return incoming
    return current


def _settlement_date(value: object) -> date | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("settlementDate must be a string")
    return date.fromisoformat(value)


def _settlement_period(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("settlementPeriod must be an integer")
    return value


def _optional_time(value: object):
    if value is None:
        return None
    return parse_timestamp(value)
