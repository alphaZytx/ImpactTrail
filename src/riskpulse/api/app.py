from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from riskpulse import __version__
from riskpulse.config import get_settings
from riskpulse.domain.documents import RawDocument, SourceType
from riskpulse.domain.signals import EventLabel, RiskSignal, SignalList
from riskpulse.domain.stress import StressRun
from riskpulse.ingestion.replay import ReplayAdapter
from riskpulse.logging import configure_logging
from riskpulse.services.factory import get_pipeline, get_repository
from riskpulse.stress_testing.portfolio import load_portfolio


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=3, max_length=8000)
    source_record_id: str | None = None
    published_at: datetime | None = None


class ReplayRequest(BaseModel):
    fixture: str = "data/demo/mixed_source_events.jsonl"


class StressRequest(BaseModel):
    signal_id: str


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(
        title="RiskPulse API",
        version=__version__,
        summary="Auditable financial risk signals and portfolio stress testing",
        description=(
            "Educational hackathon prototype. Outputs are illustrative and are not investment "
            "advice or regulatory stress-test results."
        ),
        license_info={"name": "MIT", "url": "https://opensource.org/license/mit"},
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:8501", "http://localhost:8501"],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.get("/healthz", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.get("/readyz", tags=["system"])
    def ready() -> dict[str, Any]:
        checks = {
            "database": True,
            "taxonomy": settings.taxonomy_path.exists(),
            "scenarios": settings.scenarios_path.exists(),
            "companies": settings.companies_path.exists(),
            "portfolio": settings.portfolio_path.exists(),
        }
        get_repository().metrics()
        if not all(checks.values()):
            raise HTTPException(status_code=503, detail={"status": "not_ready", "checks": checks})
        return {"status": "ready", "checks": checks}

    @app.post(
        "/api/v1/analyze",
        response_model=list[RiskSignal],
        status_code=status.HTTP_201_CREATED,
        tags=["signals"],
    )
    def analyze(request: AnalyzeRequest) -> list[RiskSignal]:
        now = datetime.now(UTC)
        raw = RawDocument(
            source_record_id=request.source_record_id or f"manual-{uuid4()}",
            source="manual",
            source_type=SourceType.NEWS,
            text=request.text,
            published_at=request.published_at or now,
            ingested_at=now,
            raw_metadata={"language": "en"},
        )
        result = get_pipeline().process_raw(raw)
        if result["duplicate"]:
            raise HTTPException(status_code=409, detail="Duplicate document")
        return cast(list[RiskSignal], result["signals"])

    @app.post("/api/v1/replays", tags=["ingestion"])
    async def replay(request: ReplayRequest) -> dict[str, Any]:
        fixture = (settings.project_root / request.fixture).resolve()
        data_root = (settings.project_root / "data").resolve()
        if data_root not in fixture.parents or not fixture.exists():
            raise HTTPException(
                status_code=400, detail="Fixture must exist under the data directory"
            )
        summary = await get_pipeline().process_adapter(ReplayAdapter(fixture))
        return {"status": "complete", **summary.as_dict()}

    @app.get("/api/v1/signals", response_model=SignalList, tags=["signals"])
    def signals(
        limit: int = Query(default=100, ge=1, le=500),
        offset: int = Query(default=0, ge=0),
        event_label: EventLabel | None = None,
        source: str | None = Query(default=None, max_length=100),
        min_impact: float | None = Query(default=None, ge=1, le=10),
        actionable: bool | None = None,
    ) -> SignalList:
        items, total = get_repository().list_signals(
            limit=limit,
            offset=offset,
            event_label=event_label.value if event_label else None,
            source=source,
            min_impact=min_impact,
            actionable=actionable,
        )
        return SignalList(items=items, total=total, limit=limit, offset=offset)

    @app.get("/api/v1/signals/{signal_id}", response_model=RiskSignal, tags=["signals"])
    def signal_detail(signal_id: str) -> RiskSignal:
        signal = get_repository().get_signal(signal_id)
        if not signal:
            raise HTTPException(status_code=404, detail="Signal not found")
        return signal

    @app.get("/api/v1/stress-tests", response_model=list[StressRun], tags=["stress"])
    def stress_runs(limit: int = Query(default=100, ge=1, le=500)) -> list[StressRun]:
        return get_repository().list_stress_runs(limit)

    @app.get("/api/v1/stress-tests/{stress_run_id}", response_model=StressRun, tags=["stress"])
    def stress_detail(stress_run_id: str) -> StressRun:
        run = get_repository().get_stress_run(stress_run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Stress run not found")
        return run

    @app.post(
        "/api/v1/stress-tests",
        response_model=StressRun,
        status_code=status.HTTP_201_CREATED,
        tags=["stress"],
    )
    def create_stress(request: StressRequest) -> StressRun:
        repository = get_repository()
        signal = repository.get_signal(request.signal_id)
        if not signal:
            raise HTTPException(status_code=404, detail="Signal not found")
        existing = repository.get_stress_run_for_signal(signal)
        if existing:
            return existing
        service = get_pipeline().stress_service
        run = service.run(signal)
        if not run:
            raise HTTPException(
                status_code=422,
                detail="Signal does not satisfy the configured stress-test trigger",
            )
        repository.save_stress_run(run, service.portfolio_version)
        return run

    @app.get("/api/v1/portfolio/summary", tags=["portfolio"])
    def portfolio_summary() -> dict[str, Any]:
        positions = load_portfolio(settings.portfolio_path)
        by_asset: dict[str, float] = {}
        by_sector: dict[str, float] = {}
        by_country: dict[str, float] = {}
        for position in positions:
            by_asset[position.asset_type.value] = (
                by_asset.get(position.asset_type.value, 0) + position.market_value
            )
            by_sector[position.sector] = by_sector.get(position.sector, 0) + position.market_value
            by_country[position.country] = (
                by_country.get(position.country, 0) + position.market_value
            )
        return {
            "position_count": len(positions),
            "market_value": round(sum(position.market_value for position in positions), 2),
            "by_asset_type": {key: round(value, 2) for key, value in by_asset.items()},
            "by_sector": {key: round(value, 2) for key, value in by_sector.items()},
            "by_country": {key: round(value, 2) for key, value in by_country.items()},
            "currency": "USD-equivalent",
            "data_classification": "synthetic",
        }

    @app.get("/api/v1/metrics/summary", tags=["system"])
    def metrics() -> dict[str, Any]:
        values = get_repository().metrics()
        pipeline = get_pipeline()
        return {
            **values,
            "active_sentiment_backend": getattr(pipeline.sentiment_analyzer, "backend", "unknown"),
            "active_event_backend": pipeline.event_classifier.backend,
            "model_version": "risk-engine-1.0.0",
            "mode": settings.env,
        }

    return app


app = create_app()
