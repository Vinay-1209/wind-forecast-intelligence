from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.analysis import AnalysisService
from app.config import Settings
from app.models import ActualRecord, ForecastRecord, IntervalResult
from app.selection import analyse
from app.timeutil import parse_timestamp

LONDON_NAME = "Europe/London"


def utc(value: str) -> datetime:
    return parse_timestamp(value)


def actual(start: str, generation: int | float, publish: str | None = None) -> ActualRecord:
    return ActualRecord(
        start=utc(start),
        generation=generation,
        settlement_date=None,
        settlement_period=None,
        publish_time=utc(publish) if publish else None,
    )


def forecast(start: str, publish: str, generation: int | float) -> ForecastRecord:
    return ForecastRecord(start=utc(start), publish_time=utc(publish), generation=generation)


def london_settings(tmp_path) -> Settings:
    return Settings(
        timezone=ZoneInfo(LONDON_NAME),
        cutoff_hour=9,
        cutoff_minute=50,
        snapshot_path=tmp_path / "snapshot.json",
        cors_origins=("http://localhost:5173",),
        elexon_base_url="https://data.elexon.co.uk/bmrs/api/v1",
    )


def one_day(
    actuals: list[ActualRecord],
    forecasts: list[ForecastRecord],
    delivery: date,
    cutoff: tuple[int, int] = (9, 50),
) -> list[IntervalResult]:
    return analyse(
        actuals,
        forecasts,
        delivery,
        delivery,
        ZoneInfo(LONDON_NAME),
        cutoff[0],
        cutoff[1],
    )


def service_for(settings: Settings, actuals, forecasts, fetched_at: str = "2026-10-28T18:00:00Z") -> AnalysisService:
    return AnalysisService(
        settings=settings,
        actuals=tuple(actuals),
        forecasts=tuple(forecasts),
        fetched_at=fetched_at,
        rejected={},
    )


def included(results: list[IntervalResult], start: str) -> IntervalResult:
    target = utc(start)
    match = next(interval for interval in results if interval.start == target)
    assert match.included, match.reason
    return match
