from datetime import date, timedelta

import pytest

from app.selection import decision_cutoff, settlement_intervals
from app.timeutil import parse_timestamp
from tests.helpers import actual, forecast, included, one_day, utc

DELIVERY = date(2026, 1, 11)
START = "2026-01-11T10:00:00Z"
HALF = "2026-01-11T10:30:00Z"


def test_forecast_published_before_cutoff_is_eligible_and_later_ones_are_not():
    results = one_day(
        [actual(START, 800)],
        [
            forecast(START, "2026-01-10T06:00:00Z", 900),
            forecast(START, "2026-01-10T09:30:00Z", 1000),
            forecast(START, "2026-01-10T09:50:00Z", 1010),
            forecast(START, "2026-01-10T09:50:01Z", 1100),
            forecast(START, "2026-01-11T09:00:00Z", 1200),
        ],
        DELIVERY,
    )
    chosen = included(results, START)
    assert chosen.forecast_mw == 1010
    assert chosen.publish_time == utc("2026-01-10T09:50:00Z")
    assert chosen.actual_mw == 800
    assert chosen.error_mw == 210
    assert chosen.publish_time <= chosen.cutoff
    eligible = [version.publish_time for version in chosen.versions if version.eligible]
    assert utc("2026-01-10T09:50:01Z") not in eligible
    assert utc("2026-01-11T09:00:00Z") not in eligible


def test_latest_eligible_forecast_wins_even_when_it_is_lower():
    results = one_day(
        [actual(START, 800)],
        [
            forecast(START, "2026-01-10T07:30:00Z", 2000),
            forecast(START, "2026-01-10T09:30:00Z", 1000),
        ],
        DELIVERY,
    )
    assert included(results, START).forecast_mw == 1000


def test_duplicate_publication_is_deterministic():
    rows = [
        forecast(START, "2026-01-10T09:30:00Z", 9),
        forecast(START, "2026-01-10T09:30:00Z", 4),
    ]
    forward = included(one_day([actual(START, 8)], rows, DELIVERY), START)
    backward = included(one_day([actual(START, 8)], list(reversed(rows)), DELIVERY), START)
    assert forward.forecast_mw == backward.forecast_mw == 4
    assert forward.error_mw == backward.error_mw == -4


def test_forecasts_join_only_the_matching_delivery_interval():
    results = one_day(
        [actual(START, 40), actual("2026-01-11T11:00:00Z", 45)],
        [forecast("2026-01-11T11:00:00Z", "2026-01-10T09:30:00Z", 50)],
        DELIVERY,
    )
    ten = next(interval for interval in results if interval.start == utc(START))
    eleven = included(results, "2026-01-11T11:00:00Z")
    assert ten.included is False
    assert ten.reason == "no_forecast_for_interval"
    assert ten.forecast_mw is None
    assert ten.error_mw is None
    assert eleven.forecast_mw == 50
    assert eleven.error_mw == 5


def test_half_hour_with_a_forecast_at_that_start_is_included():
    results = one_day(
        [actual(HALF, 700)],
        [forecast(HALF, "2026-01-10T09:30:00Z", 5)],
        DELIVERY,
    )
    chosen = included(results, HALF)
    assert chosen.forecast_mw == 5
    assert chosen.error_mw == 5 - 700


def test_missing_forecast_does_not_become_zero():
    results = one_day([actual(START, 800)], [], DELIVERY)
    interval = next(item for item in results if item.start == utc(START))
    assert interval.included is False
    assert interval.reason == "no_forecast_for_interval"
    assert interval.forecast_mw is None
    assert interval.error_mw is None
    assert interval.actual_mw == 800


def test_missing_actual_does_not_become_zero():
    results = one_day([], [forecast(START, "2026-01-10T09:30:00Z", 1000)], DELIVERY)
    interval = next(item for item in results if item.start == utc(START))
    assert interval.included is False
    assert interval.reason == "no_actual"
    assert interval.actual_mw is None
    assert interval.forecast_mw is None
    assert interval.error_mw is None
    assert any(version.generation == 1000 for version in interval.versions)


def test_forecasts_published_only_after_the_cutoff_are_excluded():
    results = one_day(
        [actual(START, 800)],
        [forecast(START, "2026-01-10T15:30:00Z", 1100)],
        DELIVERY,
    )
    interval = next(item for item in results if item.start == utc(START))
    assert interval.reason == "no_eligible_forecast"
    assert interval.forecast_mw is None
    assert interval.error_mw is None
    assert interval.versions[0].eligible is False


def test_actual_zero_remains_a_real_observation():
    results = one_day(
        [actual(START, 0)],
        [forecast(START, "2026-01-10T09:30:00Z", 10)],
        DELIVERY,
    )
    chosen = included(results, START)
    assert chosen.actual_mw == 0
    assert chosen.error_mw == 10


def test_january_settlement_day_is_midnight_to_half_past_eleven_utc():
    from zoneinfo import ZoneInfo

    slots = settlement_intervals(DELIVERY, ZoneInfo("Europe/London"))
    assert len(slots) == 48
    assert slots[0] == utc("2026-01-11T00:00:00Z")
    assert slots[-1] == utc("2026-01-11T23:30:00Z")
    assert all(right - left == timedelta(minutes=30) for left, right in zip(slots, slots[1:]))


def test_february_delivery_uses_the_january_decision_cutoff():
    start = "2026-02-01T00:00:00Z"
    results = one_day(
        [actual(start, 100)],
        [
            forecast(start, "2026-01-31T09:30:00Z", 90),
            forecast(start, "2026-01-31T11:30:00Z", 80),
        ],
        date(2026, 2, 1),
    )
    chosen = included(results, start)
    assert chosen.decision_date == date(2026, 1, 31)
    assert chosen.forecast_mw == 90
    assert chosen.cutoff == utc("2026-01-31T09:50:00Z")
    assert chosen.error_mw == -10


def test_first_january_delivery_ignores_the_late_morning_forecast():
    start = "2026-01-02T23:00:00Z"
    results = one_day(
        [actual(start, 70)],
        [
            forecast(start, "2025-12-31T22:30:00Z", 50),
            forecast(start, "2026-01-01T09:30:00Z", 70),
            forecast(start, "2026-01-01T11:30:00Z", 80),
        ],
        date(2026, 1, 2),
    )
    chosen = included(results, start)
    assert chosen.decision_date == date(2026, 1, 1)
    assert chosen.publish_time == utc("2026-01-01T09:30:00Z")
    assert chosen.error_mw == 0


def test_summer_cutoff_is_converted_from_london_time():
    from zoneinfo import ZoneInfo

    start = "2026-07-02T09:00:00Z"
    results = one_day(
        [actual(start, 100)],
        [
            forecast(start, "2026-07-01T08:50:00Z", 80),
            forecast(start, "2026-07-01T09:50:00Z", 70),
        ],
        date(2026, 7, 2),
    )
    chosen = included(results, start)
    assert chosen.cutoff == utc("2026-07-01T08:50:00Z")
    assert chosen.forecast_mw == 80
    slots = settlement_intervals(date(2026, 7, 2), ZoneInfo("Europe/London"))
    assert slots[0] == utc("2026-07-01T23:00:00Z")
    assert slots[-1] == utc("2026-07-02T22:30:00Z")
    assert decision_cutoff(date(2026, 7, 2), ZoneInfo("Europe/London"), 9, 50) == chosen.cutoff


@pytest.mark.parametrize(
    ("publish", "eligible"),
    [
        ("2026-01-10T09:49:59Z", True),
        ("2026-01-10T09:50:00Z", True),
        ("2026-01-10T09:50:01Z", False),
    ],
)
def test_cutoff_boundary_is_inclusive(publish, eligible):
    results = one_day(
        [actual(START, 10)],
        [forecast(START, publish, 12)],
        DELIVERY,
    )
    interval = next(item for item in results if item.start == utc(START))
    assert interval.included is eligible
    assert interval.versions[0].eligible is eligible
