"""Pydantic schemas for Data Foundation API."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class AuditLogCreate(BaseModel):
    service: str
    action: str
    actor: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    detail: dict = Field(default_factory=dict)
    confidence_score: float | None = None
    outcome: str = "success"


class AuditLogResponse(AuditLogCreate):
    id: UUID
    timestamp: datetime

    model_config = {"from_attributes": True}


class HealthCheckResponse(BaseModel):
    service: str
    status: str
    version: str
