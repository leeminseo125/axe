"""poQat Quality Verification Engine - System & Agent health monitoring daemon."""

import asyncio
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from shared_infra.database import get_db
from shared_infra.config import get_settings
from shared_infra.data_foundation.models import ServiceHealth, AgentHealth
from shared_infra.poqat_monitor.schemas import (
    ServiceHealthReport,
    ServiceHealthResponse,
    AgentHealthReport,
    AgentHealthResponse,
    SystemOverview,
)

settings = get_settings()

MONITORED_SERVICES = {
    "axengine": f"http://axengine:{settings.axengine_port}/health",
    "axe-poe": f"http://axe-poe:{settings.axe_poe_port}/health",
    "policy-engine": f"http://policy-engine:{settings.policy_engine_port}/health",
    "data-foundation": f"http://data-foundation:{settings.data_foundation_port}/health",
}

_monitor_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _monitor_task
    _monitor_task = asyncio.create_task(_health_check_loop())
    yield
    if _monitor_task:
        _monitor_task.cancel()


app = FastAPI(title="AXEworks poQat Monitor", version="1.0.0", lifespan=lifespan)


async def _health_check_loop():
    """Background daemon that checks service health every 30 seconds."""
    from shared_infra.database import async_session_factory

    while True:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                async with async_session_factory() as db:
                    for name, url in MONITORED_SERVICES.items():
                        report = await _check_service(client, name, url)
                        record = ServiceHealth(**report.model_dump())
                        db.add(record)
                    await db.commit()
        except Exception:
            pass
        await asyncio.sleep(30)


async def _check_service(client: httpx.AsyncClient, name: str, url: str) -> ServiceHealthReport:
    try:
        start = datetime.utcnow()
        resp = await client.get(url)
        latency = (datetime.utcnow() - start).total_seconds() * 1000
        status = "healthy" if resp.status_code == 200 else "degraded"
        return ServiceHealthReport(
            service_name=name, status=status, latency_ms=latency
        )
    except Exception as e:
        return ServiceHealthReport(
            service_name=name, status="unhealthy", error_count=1, detail={"error": str(e)}
        )


@app.get("/health")
async def health():
    return {"service": "poqat-monitor", "status": "healthy", "version": "1.0.0"}


@app.post("/services/report", response_model=ServiceHealthResponse)
async def report_service_health(body: ServiceHealthReport, db: AsyncSession = Depends(get_db)):
    record = ServiceHealth(**body.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@app.get("/services", response_model=list[ServiceHealthResponse])
async def list_service_health(db: AsyncSession = Depends(get_db)):
    """Get latest health record per service."""
    subq = (
        select(ServiceHealth.service_name, func.max(ServiceHealth.checked_at).label("latest"))
        .group_by(ServiceHealth.service_name)
        .subquery()
    )
    query = (
        select(ServiceHealth)
        .join(
            subq,
            (ServiceHealth.service_name == subq.c.service_name)
            & (ServiceHealth.checked_at == subq.c.latest),
        )
    )
    result = await db.execute(query)
    return result.scalars().all()


@app.post("/agents/report", response_model=AgentHealthResponse)
async def report_agent_health(body: AgentHealthReport, db: AsyncSession = Depends(get_db)):
    record = AgentHealth(**body.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@app.get("/agents", response_model=list[AgentHealthResponse])
async def list_agent_health(db: AsyncSession = Depends(get_db)):
    subq = (
        select(AgentHealth.agent_name, func.max(AgentHealth.checked_at).label("latest"))
        .group_by(AgentHealth.agent_name)
        .subquery()
    )
    query = (
        select(AgentHealth)
        .join(
            subq,
            (AgentHealth.agent_name == subq.c.agent_name)
            & (AgentHealth.checked_at == subq.c.latest),
        )
    )
    result = await db.execute(query)
    return result.scalars().all()


@app.get("/overview", response_model=SystemOverview)
async def system_overview(db: AsyncSession = Depends(get_db)):
    services = (await db.execute(
        select(ServiceHealth)
        .where(ServiceHealth.checked_at > datetime.utcnow() - timedelta(minutes=5))
        .order_by(desc(ServiceHealth.checked_at))
    )).scalars().all()

    # Deduplicate to latest per service
    seen = {}
    for s in services:
        if s.service_name not in seen:
            seen[s.service_name] = s
    unique_services = list(seen.values())

    agents = (await db.execute(
        select(AgentHealth)
        .where(AgentHealth.checked_at > datetime.utcnow() - timedelta(minutes=5))
        .order_by(desc(AgentHealth.checked_at))
    )).scalars().all()

    seen_agents = {}
    for a in agents:
        if a.agent_name not in seen_agents:
            seen_agents[a.agent_name] = a
    unique_agents = list(seen_agents.values())

    return SystemOverview(
        total_services=len(unique_services),
        healthy_services=sum(1 for s in unique_services if s.status == "healthy"),
        degraded_services=sum(1 for s in unique_services if s.status == "degraded"),
        unhealthy_services=sum(1 for s in unique_services if s.status == "unhealthy"),
        total_agents=len(unique_agents),
        healthy_agents=sum(1 for a in unique_agents if a.status == "healthy"),
        services=unique_services,
        agents=unique_agents,
    )
