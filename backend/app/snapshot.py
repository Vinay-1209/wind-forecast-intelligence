from __future__ import annotations

import gzip
import json
import logging

from app.analysis import AnalysisService
from app.config import Settings
from app.normalize import normalise_actuals, normalise_forecasts

logger = logging.getLogger(__name__)


def _read_payload(path) -> dict:
    raw = path.read_bytes()
    if path.suffix == ".gz" or raw.startswith(b"\x1f\x8b"):
        raw = gzip.decompress(raw)
    return json.loads(raw)


def load_service(settings: Settings) -> AnalysisService:
    payload = _read_payload(settings.snapshot_path)
    actuals, actual_rejected = normalise_actuals(payload["actuals"])
    forecasts, forecast_rejected = normalise_forecasts(payload["forecasts"])
    return AnalysisService(
        settings=settings,
        actuals=tuple(actuals),
        forecasts=tuple(forecasts),
        fetched_at=payload.get("fetched_at"),
        rejected={**actual_rejected, **forecast_rejected},
    )


def try_load_service(settings: Settings) -> AnalysisService | None:
    if not settings.snapshot_path.exists():
        logger.warning("Snapshot not found at %s", settings.snapshot_path)
        return None
    try:
        return load_service(settings)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        logger.error("Could not load snapshot: %s", exc)
        return None
