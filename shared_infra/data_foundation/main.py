"""Data Foundation Engine - Standardized data access and audit logging."""

from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from shared_infra.database import get_db
from shared_infra.data_foundation.models import AuditLog
from shared_infra.data_foundation.schemas import AuditLogCreate, AuditLogResponse, HealthCheckResponse

app = FastAPI(title="AXEworks Data Foundation Engine", version="1.0.0")


@app.get("/health", response_model=HealthCheckResponse)
async def health():
    return HealthCheckResponse(service="data-foundation", status="healthy", version="1.0.0")


@app.post("/audit", response_model=AuditLogResponse)
async def create_audit_log(entry: AuditLogCreate, db: AsyncSession = Depends(get_db)):
    log = AuditLog(**entry.model_dump())
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


@app.get("/audit", response_model=list[AuditLogResponse])
async def list_audit_logs(
    service: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    query = select(AuditLog).order_by(desc(AuditLog.timestamp)).limit(limit)
    if service:
        query = query.where(AuditLog.service == service)
    result = await db.execute(query)
    return result.scalars().all()
