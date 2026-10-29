from fastapi.testclient import TestClient

from app.main import create_app
from tests.helpers import actual, forecast, london_settings, service_for

START = "2026-01-11T10:00:00Z"
HALF = "2026-01-11T10:30:00Z"


def test_health_reports_the_snapshot(tmp_path):
    client = _client(tmp_path)
    response = client.get("/api/health")
    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "ok"
    assert body["cutoff_time"] == "09:50"
    assert body["timezone"] == "Europe/London"
    assert body["delivery_from"] == "2026-01-02"
    assert body["delivery_to"] == "2026-02-01"
    assert body["actual_rows"] == 2
    assert body["forecast_rows"] == 4


def test_missing_snapshot_is_unavailable():
    client = TestClient(create_app(load_snapshot=False))
    for path in (
        "/api/health",
        "/api/analysis/summary",
        "/api/analysis/timeseries",
        "/api/analysis/data-quality",
        "/api/analysis/forecast-details?start=2026-01-11T10:00:00Z",
    ):
        response = client.get(path)
        assert response.status_code == 503
        assert "snapshot" in response.json()["detail"].lower()


def test_summary_uses_only_the_matched_pair(tmp_path):
    body = _client(tmp_path).get(
        "/api/analysis/summary",
        params={"delivery_from": "2026-01-11", "delivery_to": "2026-01-11"},
    ).json()
    assert body["included_pairs"] == 1
    assert body["mae_mw"] == 200
    assert body["rmse_mw"] == 200
    assert body["mbe_mw"] == 200
    assert body["bias_label"] == "overforecast"
    assert body["metrics_based_on_incomplete_hourly_coverage"] is True
    assert body["rules"]["cutoff_time"] == "09:50"
    assert body["rules"]["alignment"] == "exact_start_time"
    assert "09:50" in body["assumption_note"]
    assert body["largest_absolute_errors"][0]["start_time"] == START
    assert body["largest_absolute_errors"][0]["error_mw"] == 200
    for key in ("mae_mw", "rmse_mw", "mbe_mw", "included_pairs", "assumption_note", "rules"):
        assert key in body


def test_timeseries_keeps_a_missing_forecast_null(tmp_path):
    points = _client(tmp_path).get(
        "/api/analysis/timeseries",
        params={"delivery_from": "2026-01-11", "delivery_to": "2026-01-11"},
    ).json()["points"]
    half = next(point for point in points if point["start_time"] == HALF)
    matched = next(point for point in points if point["start_time"] == START)
    assert half["actual_mw"] == 700
    assert half["forecast_mw"] is None
    assert half["error_mw"] is None
    assert half["included"] is False
    assert half["reason"] == "no_forecast_for_interval"
    assert matched["forecast_mw"] == 1000
    assert matched["actual_mw"] == 800
    assert matched["publish_time"] == "2026-01-10T09:30:00Z"


def test_forecast_details_show_which_publications_were_excluded(tmp_path):
    body = _client(tmp_path).get("/api/analysis/forecast-details", params={"start": START}).json()
    assert body["included"] is True
    assert body["decision_date"] == "2026-01-10"
    assert body["cutoff_time"] == "2026-01-10T09:50:00Z"
    assert body["forecast_mw"] == 1000
    assert body["actual_mw"] == 800
    assert body["error_mw"] == 200
    assert body["absolute_error_mw"] == 200
    selected = [version for version in body["versions"] if version["selected"]]
    assert selected == [
        {
            "publish_time": "2026-01-10T09:30:00Z",
            "generation_mw": 1000,
            "eligible": True,
            "selected": True,
        }
    ]
    rejected = next(version for version in body["versions"] if version["publish_time"] == "2026-01-11T09:00:00Z")
    assert rejected["eligible"] is False
    assert rejected["selected"] is False


def test_invalid_and_empty_requests(tmp_path):
    client = _client(tmp_path)
    ordered = client.get(
        "/api/analysis/summary",
        params={"delivery_from": "2026-01-20", "delivery_to": "2026-01-10"},
    )
    assert ordered.status_code == 422
    outside = client.get(
        "/api/analysis/summary",
        params={"delivery_from": "2026-01-02", "delivery_to": "2026-03-01"},
    )
    assert outside.status_code == 422
    assert "2026-02-01" in outside.json()["detail"]
    bad_clock = client.get("/api/analysis/forecast-details", params={"start": "2026-01-11T10:15:00Z"})
    assert bad_clock.status_code == 422
    naive = client.get("/api/analysis/forecast-details", params={"start": "not-a-timestamp"})
    assert naive.status_code == 422
    outside_day = client.get(
        "/api/analysis/forecast-details",
        params={"start": "2026-03-01T00:00:00Z"},
    )
    assert outside_day.status_code == 422

    empty = TestClient(create_app(service_for(london_settings(tmp_path), [], [])))
    body = empty.get(
        "/api/analysis/summary",
        params={"delivery_from": "2026-01-11", "delivery_to": "2026-01-11"},
    ).json()
    assert body["included_pairs"] == 0
    assert body["mae_mw"] is None
    assert body["rmse_mw"] is None
    assert body["mbe_mw"] is None
    quality = empty.get(
        "/api/analysis/data-quality",
        params={"delivery_from": "2026-01-11", "delivery_to": "2026-01-11"},
    ).json()
    assert quality["included_pairs"] == 0
    assert quality["expected_intervals"] == 48


def _client(tmp_path) -> TestClient:
    settings = london_settings(tmp_path)
    service = service_for(
        settings,
        [actual(START, 800), actual(HALF, 700)],
        [
            forecast(START, "2026-01-10T06:00:00Z", 900),
            forecast(START, "2026-01-10T09:30:00Z", 1000),
            forecast(START, "2026-01-10T15:30:00Z", 1100),
            forecast(START, "2026-01-11T09:00:00Z", 1200),
        ],
    )
    return TestClient(create_app(service))
