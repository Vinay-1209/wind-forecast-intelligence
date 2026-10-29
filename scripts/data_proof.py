"""Live one-day check of the same selection code the API uses.

Run from the repository root:
    python scripts/data_proof.py
"""

from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import load_settings  # noqa: E402
from app.elexon import ElexonClient, require_publish_window, require_wind_actuals  # noqa: E402
from app.normalize import normalise_actuals, normalise_forecasts  # noqa: E402
from app.selection import analyse  # noqa: E402
from app.timeutil import format_z, parse_timestamp  # noqa: E402

DECISION = date(2026, 1, 10)
DELIVERY = date(2026, 1, 11)
FOCUS = "2026-01-11T10:00:00Z"


def main() -> None:
    settings = load_settings()
    client = ElexonClient(settings.elexon_base_url)
    actual_rows = client.get_stream(
        "/datasets/FUELHH/stream",
        {
            "settlementDateFrom": DELIVERY.isoformat(),
            "settlementDateTo": DELIVERY.isoformat(),
            "fuelType": "WIND",
        },
    )
    require_wind_actuals(actual_rows, DELIVERY, DELIVERY)
    publish_from = datetime(2026, 1, 10, tzinfo=timezone.utc)
    publish_to = datetime(2026, 1, 12, tzinfo=timezone.utc)
    forecast_rows = client.get_stream(
        "/datasets/WINDFOR/stream",
        {
            "publishDateTimeFrom": format_z(publish_from),
            "publishDateTimeTo": format_z(publish_to),
        },
    )
    require_publish_window(forecast_rows, publish_from, publish_to)
    actuals, _ = normalise_actuals(actual_rows)
    forecasts, _ = normalise_forecasts(forecast_rows)
    intervals = analyse(
        actuals,
        forecasts,
        DELIVERY,
        DELIVERY,
        settings.timezone,
        settings.cutoff_hour,
        settings.cutoff_minute,
    )
    included = [interval for interval in intervals if interval.included]
    half_hours = [interval for interval in intervals if interval.reason == "no_forecast_for_interval"]
    focus = next(interval for interval in intervals if interval.start == parse_timestamp(FOCUS))
    print(f"decision_date {DECISION.isoformat()} cutoff {format_z(focus.cutoff)}")
    print(f"delivery_settlement_date {DELIVERY.isoformat()}")
    print(f"actual_rows {len(actuals)} forecast_rows_in_window {len(forecasts)}")
    print(f"matched_hourly {len(included)} excluded_without_forecast {len(half_hours)}")
    print("focus_interval versions (observed):")
    for version in focus.versions:
        print(
            f"  publish {format_z(version.publish_time)} generation {version.generation} "
            f"eligible {version.eligible} selected {version.selected}"
        )
    if not focus.included:
        raise SystemExit(f"focus interval was excluded: {focus.reason}")
    print(
        "focus_selected "
        f"publish {format_z(focus.publish_time)} forecast {focus.forecast_mw} "
        f"actual {focus.actual_mw} error {focus.error_mw}"
    )
    if format_z(focus.publish_time) != "2026-01-10T09:30:00Z":
        raise SystemExit(
            "Expected the 09:30 publication for this delivery interval. "
            f"Got {format_z(focus.publish_time)}."
        )
    if any(interval.publish_time > interval.cutoff for interval in included):
        raise SystemExit("Selected a forecast published after the cutoff.")
    if any(interval.start.minute == 30 for interval in included):
        raise SystemExit("Included a :30 interval. This live day was expected to match forecasts only on the hour.")


if __name__ == "__main__":
    main()
