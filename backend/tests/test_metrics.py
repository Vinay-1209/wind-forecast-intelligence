import math
from datetime import date, datetime, timezone

from app.metrics import calculate_metrics
from app.models import IntervalResult


def test_metrics_match_a_manual_example():
    # errors are +2 and -3. MAE 2.5, RMSE sqrt(6.5), MBE -0.5.
    metrics = calculate_metrics([_included(2), _included(-3, minute=30)])
    assert metrics.pair_count == 2
    assert metrics.mae == 2.5
    assert metrics.mbe == -0.5
    assert metrics.rmse == math.sqrt(6.5)
    assert metrics.bias_label == "underforecast"


def test_positive_bias_means_the_forecast_was_higher_than_actual():
    metrics = calculate_metrics([_included(4)])
    assert metrics.mbe == 4
    assert metrics.mae == 4
    assert metrics.rmse == 4
    assert metrics.bias_label == "overforecast"


def test_no_pairs_do_not_become_zero_error():
    metrics = calculate_metrics([_excluded(), _missing()])
    assert metrics.pair_count == 0
    assert metrics.mae is None
    assert metrics.rmse is None
    assert metrics.mbe is None
    assert metrics.bias_label is None


def test_excluded_intervals_do_not_change_the_average():
    metrics = calculate_metrics([_included(2), _excluded(error=100)])
    assert metrics.pair_count == 1
    assert metrics.mae == 2
    assert metrics.mbe == 2


def test_a_real_zero_error_is_kept():
    metrics = calculate_metrics([_included(0)])
    assert metrics.pair_count == 1
    assert metrics.mae == 0
    assert metrics.mbe == 0
    assert metrics.bias_label == "no_bias"


def _interval(error, included: bool, minute: int, reason: str | None) -> IntervalResult:
    start = datetime(2026, 1, 11, 10, minute, tzinfo=timezone.utc)
    return IntervalResult(
        start=start,
        decision_date=date(2026, 1, 10),
        delivery_date=date(2026, 1, 11),
        cutoff=datetime(2026, 1, 10, 9, 50, tzinfo=timezone.utc),
        actual_mw=0 if included else None,
        forecast_mw=error if included else None,
        publish_time=datetime(2026, 1, 10, 9, 30, tzinfo=timezone.utc) if included else None,
        error_mw=error if included or error is not None else None,
        included=included,
        reason=reason,
        versions=(),
    )


def _included(error: int | float, minute: int = 0) -> IntervalResult:
    return _interval(error, True, minute, None)


def _excluded(error: int | float | None = None) -> IntervalResult:
    interval = _interval(0, False, 30, "no_forecast_for_interval")
    return IntervalResult(
        start=interval.start,
        decision_date=interval.decision_date,
        delivery_date=interval.delivery_date,
        cutoff=interval.cutoff,
        actual_mw=800,
        forecast_mw=None,
        publish_time=None,
        error_mw=error,
        included=False,
        reason="no_forecast_for_interval",
        versions=(),
    )


def _missing() -> IntervalResult:
    return _interval(None, False, 0, "missing_interval")
