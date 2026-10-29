"""Download the January 2026 study window and write data/snapshot.json.

The file stores the raw Elexon rows. The API normalises them on load, so the
same file and cutoff produce the same metrics.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import DELIVERY_FROM, DELIVERY_TO, load_settings  # noqa: E402
from app.elexon import ElexonClient, require_publish_window, require_wind_actuals  # noqa: E402
from app.snapshot import load_service  # noqa: E402
from app.timeutil import format_z, parse_timestamp  # noqa: E402

PUBLISH_FROM = datetime(2025, 12, 31, tzinfo=timezone.utc)
PUBLISH_TO = datetime(2026, 2, 2, tzinfo=timezone.utc)


def main() -> None:
    settings = load_settings()
    client = ElexonClient(settings.elexon_base_url, timeout_seconds=120)
    actual_params = {
        "settlementDateFrom": DELIVERY_FROM.isoformat(),
        "settlementDateTo": DELIVERY_TO.isoformat(),
        "fuelType": "WIND",
    }
    forecast_params = {
        "publishDateTimeFrom": format_z(PUBLISH_FROM),
        "publishDateTimeTo": format_z(PUBLISH_TO),
    }
    actuals = client.get_stream("/datasets/FUELHH/stream", actual_params)
    require_wind_actuals(actuals, DELIVERY_FROM, DELIVERY_TO)
    forecasts = client.get_stream("/datasets/WINDFOR/stream", forecast_params)
    require_publish_window(forecasts, PUBLISH_FROM, PUBLISH_TO)

    payload = {
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": settings.elexon_base_url,
        "requests": [
            {"path": "/datasets/FUELHH/stream", "params": actual_params, "rows": len(actuals)},
            {"path": "/datasets/WINDFOR/stream", "params": forecast_params, "rows": len(forecasts)},
        ],
        "actuals": actuals,
        "forecasts": forecasts,
    }
    settings.snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    settings.snapshot_path.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {settings.snapshot_path} actuals={len(actuals)} forecasts={len(forecasts)}")

    service = load_service(settings)
    focus = next(
        interval
        for interval in service.intervals(DELIVERY_FROM, DELIVERY_TO)
        if interval.start == parse_timestamp("2026-01-11T10:00:00Z")
    )
    if not focus.included or focus.publish_time > focus.cutoff:
        raise SystemExit("snapshot failed the decision-time check")
    if focus.error_mw != focus.forecast_mw - focus.actual_mw:
        raise SystemExit("snapshot error does not equal forecast minus actual")
    print(
        "focus 2026-01-11T10:00:00Z "
        f"publish {format_z(focus.publish_time)} forecast {focus.forecast_mw} "
        f"actual {focus.actual_mw} error {focus.error_mw}"
    )


if __name__ == "__main__":
    main()
