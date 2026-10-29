from __future__ import annotations

import math
from dataclasses import dataclass

from app.models import IntervalResult


@dataclass(frozen=True)
class Metrics:
    pair_count: int
    mae: float | None
    rmse: float | None
    mbe: float | None

    @property
    def bias_label(self) -> str | None:
        if self.mbe is None:
            return None
        if self.mbe > 0:
            return "overforecast"
        if self.mbe < 0:
            return "underforecast"
        return "no_bias"


def calculate_metrics(intervals: list[IntervalResult]) -> Metrics:
    """Error is forecast minus actual. Empty input does not become a zero error."""
    errors = [interval.error_mw for interval in intervals if interval.included]
    if any(error is None for error in errors):
        raise ValueError("an included interval is missing an error")
    if not errors:
        return Metrics(pair_count=0, mae=None, rmse=None, mbe=None)
    count = len(errors)
    mae = sum(abs(error) for error in errors) / count
    mbe = sum(errors) / count
    rmse = math.sqrt(sum(error * error for error in errors) / count)
    return Metrics(pair_count=count, mae=mae, rmse=rmse, mbe=mbe)
