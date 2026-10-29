from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class ActualRecord:
    start: datetime
    generation: int | float
    settlement_date: date | None
    settlement_period: int | None
    publish_time: datetime | None


@dataclass(frozen=True)
class ForecastRecord:
    start: datetime
    publish_time: datetime
    generation: int | float


@dataclass(frozen=True)
class ForecastVersion:
    publish_time: datetime
    generation: int | float
    eligible: bool
    selected: bool


@dataclass(frozen=True)
class IntervalResult:
    start: datetime
    decision_date: date
    delivery_date: date
    cutoff: datetime
    actual_mw: int | float | None
    forecast_mw: int | float | None
    publish_time: datetime | None
    error_mw: int | float | None
    included: bool
    reason: str | None
    versions: tuple[ForecastVersion, ...]
