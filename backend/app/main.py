from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.analysis import AnalysisService
from app.config import Settings, load_settings
from app.routes import router
from app.snapshot import try_load_service


def create_app(
    service: AnalysisService | None = None,
    settings: Settings | None = None,
    *,
    load_snapshot: bool = True,
) -> FastAPI:
    resolved = service.settings if service is not None else (settings or load_settings())
    if service is None and load_snapshot:
        service = try_load_service(resolved)
    app = FastAPI(title="Wind Forecast Intelligence", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(resolved.cors_origins),
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    app.state.service = service
    app.include_router(router, prefix="/api")
    return app


app = create_app()


def main() -> None:
    import uvicorn

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
