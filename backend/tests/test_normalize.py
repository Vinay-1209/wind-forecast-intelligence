import pytest

from app.normalize import normalise_actuals, normalise_forecasts
from tests.helpers import utc

DAY = "2026-01-11T10:00:00Z"


def test_wind_filter_drops_other_fuels():
    records, rejected = normalise_actuals(
        [
            _actual_row("WIND", 100),
            _actual_row("CCGT", 500),
            _actual_row("wind", 50),
        ]
    )
    assert [record.generation for record in records] == [100]
    assert rejected["other_fuel"] == 2


def test_missing_generation_is_dropped_rather_than_zero():
    records, rejected = normalise_actuals(
        [
            _actual_row("WIND", None),
            _actual_row("WIND", "100"),
            _actual_row("WIND", True),
            _actual_row("WIND", float("nan")),
        ]
    )
    assert records == []
    assert rejected["invalid_actual"] == 4


def test_naive_timestamp_is_rejected():
    row = _actual_row("WIND", 10)
    row["startTime"] = "2026-01-11T10:00:00"
    records, rejected = normalise_actuals([row])
    assert records == []
    assert rejected["invalid_actual"] == 1


def test_later_actual_publication_replaces_an_earlier_one():
    rows = [
        _actual_row("WIND", 10, publish="2026-01-11T10:30:00Z"),
        _actual_row("WIND", 12, publish="2026-01-11T11:00:00Z"),
    ]
    forward, _ = normalise_actuals(rows)
    backward, rejected = normalise_actuals(list(reversed(rows)))
    assert forward[0].generation == backward[0].generation == 12
    assert rejected["duplicate_actual_conflict"] == 1


def test_conflicting_forecast_duplicate_keeps_the_lower_generation():
    rows = [
        _forecast_row(9, "2026-01-10T09:30:00Z"),
        _forecast_row(4, "2026-01-10T09:30:00Z"),
    ]
    forward, forward_rejected = normalise_forecasts(rows)
    backward, backward_rejected = normalise_forecasts(list(reversed(rows)))
    assert forward[0].generation == backward[0].generation == 4
    assert forward_rejected["duplicate_forecast_conflict"] == 1
    assert backward_rejected["duplicate_forecast_conflict"] == 1


def test_identical_forecast_duplicates_collapse_without_a_conflict():
    rows = [
        _forecast_row(4, "2026-01-10T09:30:00Z"),
        _forecast_row(4, "2026-01-10T09:30:00Z"),
    ]
    records, rejected = normalise_forecasts(rows)
    assert len(records) == 1
    assert rejected["duplicate_forecast_conflict"] == 0
    assert records[0].start == utc(DAY)


def _actual_row(fuel: str, generation, publish: str = "2026-01-11T10:30:00Z") -> dict:
    return {
        "dataset": "FUELHH",
        "fuelType": fuel,
        "startTime": DAY,
        "publishTime": publish,
        "settlementDate": "2026-01-11",
        "settlementPeriod": 21,
        "generation": generation,
    }


def _forecast_row(generation: int, publish: str) -> dict:
    return {
        "dataset": "WINDFOR",
        "startTime": DAY,
        "publishTime": publish,
        "generation": generation,
    }


def test_actual_conflict_at_the_same_publication_time_is_deterministic():
    rows = [
        _actual_row("WIND", 9, publish="2026-01-11T10:30:00Z"),
        _actual_row("WIND", 4, publish="2026-01-11T10:30:00Z"),
    ]
    forward, _ = normalise_actuals(rows)
    backward, _ = normalise_actuals(list(reversed(rows)))
    assert forward[0].generation == backward[0].generation == 4


@pytest.mark.parametrize("generation", [0, 0.0])
def test_real_zero_generation_is_kept(generation):
    records, rejected = normalise_actuals([_actual_row("WIND", generation)])
    assert rejected["invalid_actual"] == 0
    assert records[0].generation == generation
    assert records[0].start == utc(DAY)
