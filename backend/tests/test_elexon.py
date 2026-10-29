import io
import json
import urllib.error
from datetime import date, datetime, timezone

import pytest

from app.elexon import (
    ElexonClient,
    ElexonError,
    parse_stream_payload,
    require_publish_window,
    require_wind_actuals,
)


def test_wrapped_and_stream_payloads_are_both_accepted():
    row = {"generation": 1}
    assert parse_stream_payload([row]) == [row]
    assert parse_stream_payload({"data": [row]}) == [row]


def test_unexpected_shape_is_rejected():
    with pytest.raises(ElexonError, match="unexpected response shape"):
        parse_stream_payload({"data": {"generation": 1}})


def test_timeout_becomes_a_safe_error(monkeypatch):
    def explode(*args, **kwargs):
        raise TimeoutError("slow")

    monkeypatch.setattr("urllib.request.urlopen", explode)
    with pytest.raises(ElexonError, match="timed out") as caught:
        ElexonClient("https://data.elexon.co.uk/bmrs/api/v1").get_stream("/datasets/FUELHH/stream", {})
    assert "slow" not in str(caught.value)


def test_http_error_hides_the_response_body(monkeypatch):
    def explode(*args, **kwargs):
        raise urllib.error.HTTPError(
            "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream",
            503,
            "unavailable",
            hdrs=None,
            fp=io.BytesIO(b"SECRET-BODY"),
        )

    monkeypatch.setattr("urllib.request.urlopen", explode)
    with pytest.raises(ElexonError, match="HTTP 503") as caught:
        ElexonClient("https://example.test").get_stream("/datasets/WINDFOR/stream", {})
    assert "SECRET-BODY" not in str(caught.value)


def test_invalid_json_is_rejected(monkeypatch):
    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: _Response(b"not-json"))
    with pytest.raises(ElexonError, match="invalid JSON"):
        ElexonClient("https://example.test").get_stream("/datasets/FUELHH/stream", {})


def test_empty_stream_is_returned_and_then_rejected_by_the_window_check(monkeypatch):
    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: _Response(b"[]"))
    rows = ElexonClient("https://example.test").get_stream("/datasets/WINDFOR/stream", {})
    assert rows == []
    with pytest.raises(ElexonError, match="no forecast rows"):
        require_publish_window(
            rows,
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            datetime(2026, 2, 1, tzinfo=timezone.utc),
        )


def test_latest_snapshot_outside_the_requested_window_is_rejected():
    rows = [
        {
            "publishTime": "2026-10-28T15:30:00Z",
            "startTime": "2026-10-28T16:00:00Z",
            "generation": 1,
        }
    ]
    with pytest.raises(ElexonError, match="outside the requested publication window"):
        require_publish_window(
            rows,
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            datetime(2026, 2, 2, tzinfo=timezone.utc),
        )


def test_actuals_must_be_wind_inside_the_settlement_window():
    with pytest.raises(ElexonError, match="fuel other than WIND"):
        require_wind_actuals(
            [_actual("CCGT", "2026-01-11")],
            date(2026, 1, 2),
            date(2026, 2, 1),
        )
    with pytest.raises(ElexonError, match="outside the requested settlement dates"):
        require_wind_actuals(
            [_actual("WIND", "2026-10-28")],
            date(2026, 1, 2),
            date(2026, 2, 1),
        )
    require_wind_actuals([_actual("WIND", "2026-01-11")], date(2026, 1, 2), date(2026, 2, 1))


def test_empty_actuals_are_rejected():
    with pytest.raises(ElexonError, match="no actual rows"):
        require_wind_actuals([], date(2026, 1, 2), date(2026, 2, 1))


class _Response:
    def __init__(self, raw: bytes) -> None:
        self.raw = raw

    def read(self) -> bytes:
        return self.raw

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _actual(fuel: str, settlement: str) -> dict:
    return {"fuelType": fuel, "settlementDate": settlement}


def test_stream_object_without_data_is_rejected():
    with pytest.raises(ElexonError, match="unexpected response shape"):
        parse_stream_payload(json.loads('{"metadata": []}'))
