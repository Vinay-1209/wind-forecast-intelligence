from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo

REPO_ROOT = Path(__file__).resolve().parents[2]

# Approved 28 October 2026. Decision dates are 1–31 January 2026.
# Delivery settlement dates are the following Elexon settlement day.
DELIVERY_FROM = date(2026, 1, 2)
DELIVERY_TO = date(2026, 2, 1)
DECISION_FROM = date(2026, 1, 1)
DECISION_TO = date(2026, 1, 31)


@dataclass(frozen=True)
class Settings:
    timezone: ZoneInfo
    cutoff_hour: int
    cutoff_minute: int
    snapshot_path: Path
    cors_origins: tuple[str, ...]
    elexon_base_url: str
    delivery_from: date = DELIVERY_FROM
    delivery_to: date = DELIVERY_TO
    decision_from: date = DECISION_FROM
    decision_to: date = DECISION_TO

    @property
    def timezone_name(self) -> str:
        return getattr(self.timezone, "key", str(self.timezone))

    @property
    def cutoff_label(self) -> str:
        return f"{self.cutoff_hour:02d}:{self.cutoff_minute:02d}"


def parse_cutoff(value: str) -> tuple[int, int]:
    parts = value.strip().split(":")
    if len(parts) != 2:
        raise ValueError("CUTOFF_TIME must look like 09:50")
    hour, minute = int(parts[0]), int(parts[1])
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError("CUTOFF_TIME is outside a valid clock time")
    return hour, minute


def load_settings() -> Settings:
    hour, minute = parse_cutoff(os.environ.get("CUTOFF_TIME", "09:50"))
    origins = tuple(
        origin.strip()
        for origin in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    )
    return Settings(
        timezone=ZoneInfo(os.environ.get("TIMEZONE", "Europe/London")),
        cutoff_hour=hour,
        cutoff_minute=minute,
        snapshot_path=Path(os.environ.get("SNAPSHOT_PATH", str(REPO_ROOT / "data" / "snapshot.json"))),
        cors_origins=origins,
        elexon_base_url=os.environ.get(
            "ELEXON_BASE_URL", "https://data.elexon.co.uk/bmrs/api/v1"
        ).rstrip("/"),
    )


def assumption_note(settings: Settings) -> str:
    return (
        f"A forecast is eligible when it was published at or before {settings.cutoff_label} "
        f"{settings.timezone_name} on the day before the delivery settlement date. "
        "The latest eligible publication is compared with the actual that has the same delivery start time. "
        "Pairs are omitted when either side is missing. Omitted intervals are not treated as zero generation."
    )
