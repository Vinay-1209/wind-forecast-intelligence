from datetime import date, datetime, timezone

import pytest

from app.config import DELIVERY_FROM, DELIVERY_TO, load_settings
from app.snapshot import load_service
from app.timeutil import parse_timestamp

FOCUS = "2026-01-11T10:00:00Z"
# Observed from the live Elexon extract on 28 October 2026.
FOCUS_FORECAST_MW = 18883
FOCUS_ACTUAL_MW = 14789
FOCUS_PUBLISH = "2026-01-10T09:30:00Z"


def test_snapshot_uses_no_forecast_published_after_its_cutoff():
    service = _service()
    intervals = service.intervals(DELIVERY_FROM, DELIVERY_TO)
    included = [interval for interval in intervals if interval.included]
    assert included
    assert all(interval.publish_time <= interval.cutoff for interval in included)
    assert all(interval.error_mw == interval.forecast_mw - interval.actual_mw for interval in included)
    hourly = [interval for interval in intervals if interval.start.astimezone(timezone.utc).minute == 0]
    half_hours = [interval for interval in intervals if interval.start.astimezone(timezone.utc).minute == 30]
    assert len(hourly) == 31 * 24
    assert len(half_hours) == 31 * 24
    assert all(interval.included for interval in hourly)
    assert all(interval.reason == "no_forecast_for_interval" for interval in half_hours)


def test_known_delivery_interval_matches_the_live_proof():
    service = _service()
    interval = next(item for item in service.intervals(date(2026, 1, 11), date(2026, 1, 11)) if item.start == parse_timestamp(FOCUS))
    assert interval.included
    assert interval.publish_time == parse_timestamp(FOCUS_PUBLISH)
    assert interval.forecast_mw == FOCUS_FORECAST_MW
    assert interval.actual_mw == FOCUS_ACTUAL_MW
    assert interval.error_mw == FOCUS_FORECAST_MW - FOCUS_ACTUAL_MW
    assert interval.cutoff == datetime(2026, 1, 10, 9, 50, tzinfo=timezone.utc)
    assert any(
        version.publish_time > interval.cutoff and not version.eligible and not version.selected
        for version in interval.versions
    )


def _service():
    path = load_settings().snapshot_path
    if not path.exists():
        pytest.skip(f"snapshot not built at {path}")
    return load_service(load_settings())
