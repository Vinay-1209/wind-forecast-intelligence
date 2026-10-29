from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime

from app.timeutil import parse_timestamp

logger = logging.getLogger(__name__)

USER_AGENT = "wind-forecast-intelligence/0.1"


class ElexonError(Exception):
    """The upstream dataset could not be used. The message is safe to show."""


class ElexonClient:
    def __init__(self, base_url: str, timeout_seconds: float = 90) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def get_stream(self, path: str, params: dict[str, str]) -> list[dict]:
        url = self.base_url + path + "?" + urllib.parse.urlencode(params)
        request = urllib.request.Request(
            url,
            headers={"Accept": "application/json", "User-Agent": USER_AGENT},
        )
        logger.info("Fetching Elexon %s", path)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read()
        except TimeoutError as exc:
            raise ElexonError("Elexon request timed out") from exc
        except urllib.error.HTTPError as exc:
            raise ElexonError(f"Elexon returned HTTP {exc.code}") from exc
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise ElexonError("Elexon request timed out") from exc
            raise ElexonError("Elexon request failed") from exc
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ElexonError("Elexon returned invalid JSON") from exc
        return parse_stream_payload(payload)


def parse_stream_payload(payload: object) -> list[dict]:
    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        rows = payload["data"]
    elif isinstance(payload, list):
        rows = payload
    else:
        raise ElexonError("Elexon returned an unexpected response shape")
    if not all(isinstance(row, dict) for row in rows):
        raise ElexonError("Elexon returned an unexpected response shape")
    return rows


def require_publish_window(rows: list[dict], start: datetime, end: datetime) -> None:
    """Reject a response whose publication times fall outside the request.

    WINDFOR ignores unknown parameters and otherwise returns the latest
    publication. That latest publication must not be analysed as January data.
    `end` is exclusive.
    """
    if not rows:
        raise ElexonError("Elexon returned no forecast rows")
    for row in rows:
        try:
            published = parse_timestamp(row["publishTime"])
        except (KeyError, ValueError) as exc:
            raise ElexonError("Elexon forecast row is missing a valid publishTime") from exc
        if published < start or published >= end:
            raise ElexonError(
                "Elexon forecast response is outside the requested publication window"
            )


def require_wind_actuals(rows: list[dict], settlement_from: date, settlement_to: date) -> None:
    if not rows:
        raise ElexonError("Elexon returned no actual rows")
    for row in rows:
        if row.get("fuelType") != "WIND":
            raise ElexonError("Elexon actuals response included a fuel other than WIND")
        try:
            settlement = date.fromisoformat(row["settlementDate"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ElexonError("Elexon actual row is missing a valid settlementDate") from exc
        if settlement < settlement_from or settlement > settlement_to:
            raise ElexonError("Elexon actuals response is outside the requested settlement dates")
