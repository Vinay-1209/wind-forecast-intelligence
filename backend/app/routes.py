from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Request

from app.analysis import AnalysisService, detail_payload
from app.schemas import (
    DataQualityResponse,
    ForecastDetailsResponse,
    HealthResponse,
    SummaryResponse,
    TimeseriesResponse,
)
from app.timeutil import parse_timestamp

router = APIRouter()


def get_service(request: Request) -> AnalysisService:
    service = request.app.state.service
    if service is None:
        raise HTTPException(
            status_code=503,
            detail="Analysis snapshot is not available. Run scripts/refresh_snapshot.py.",
        )
    return service


def resolve_range(
    service: AnalysisService,
    delivery_from: date | None,
    delivery_to: date | None,
) -> tuple[date, date]:
    start = delivery_from or service.settings.delivery_from
    end = delivery_to or service.settings.delivery_to
    if start > end:
        raise HTTPException(
            status_code=422,
            detail="delivery_from must be on or before delivery_to",
        )
    window_start = service.settings.delivery_from
    window_end = service.settings.delivery_to
    if start < window_start or end > window_end:
        raise HTTPException(
            status_code=422,
            detail=(
                "Delivery dates must stay within "
                f"{window_start.isoformat()} and {window_end.isoformat()}"
            ),
        )
    return start, end


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    service = request.app.state.service
    if service is None:
        raise HTTPException(
            status_code=503,
            detail="Analysis snapshot is not available. Run scripts/refresh_snapshot.py.",
        )
    return HealthResponse(
        status="ok",
        snapshot_fetched_at=service.fetched_at,
        actual_rows=len(service.actuals),
        forecast_rows=len(service.forecasts),
        delivery_from=service.settings.delivery_from,
        delivery_to=service.settings.delivery_to,
        cutoff_time=service.settings.cutoff_label,
        timezone=service.settings.timezone_name,
    )


@router.get("/analysis/summary", response_model=SummaryResponse)
def summary(
    request: Request,
    delivery_from: date | None = None,
    delivery_to: date | None = None,
) -> SummaryResponse:
    service = get_service(request)
    start, end = resolve_range(service, delivery_from, delivery_to)
    return SummaryResponse.model_validate(service.summary(start, end))


@router.get("/analysis/timeseries", response_model=TimeseriesResponse)
def timeseries(
    request: Request,
    delivery_from: date | None = None,
    delivery_to: date | None = None,
) -> TimeseriesResponse:
    service = get_service(request)
    start, end = resolve_range(service, delivery_from, delivery_to)
    return TimeseriesResponse.model_validate(service.timeseries(start, end))


@router.get("/analysis/forecast-details", response_model=ForecastDetailsResponse)
def forecast_details(request: Request, start: str) -> ForecastDetailsResponse:
    service = get_service(request)
    try:
        start_time = parse_timestamp(start)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="start must be a timezone-aware timestamp") from exc
    if start_time.second or start_time.microsecond or start_time.minute not in (0, 30):
        raise HTTPException(status_code=422, detail="start must be a 30-minute settlement interval")
    interval = service.forecast_details(start_time)
    if interval is None:
        raise HTTPException(
            status_code=422,
            detail=(
                "start must fall in a delivery settlement date from "
                f"{service.settings.delivery_from.isoformat()} to "
                f"{service.settings.delivery_to.isoformat()}"
            ),
        )
    return ForecastDetailsResponse.model_validate(detail_payload(interval))


@router.get("/analysis/data-quality", response_model=DataQualityResponse)
def data_quality(
    request: Request,
    delivery_from: date | None = None,
    delivery_to: date | None = None,
) -> DataQualityResponse:
    service = get_service(request)
    start, end = resolve_range(service, delivery_from, delivery_to)
    return DataQualityResponse.model_validate(service.data_quality(start, end))
