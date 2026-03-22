"""Pydantic schemas for poQat Quality Monitor."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class ServiceHealthReport(BaseModel):
    service_name: str
    status: str = "healthy"
    latency_ms: float | None = None
    error_count: int = 0
    detail: dict = Field(default_factory=dict)


class ServiceHealthResponse(ServiceHealthReport):
    id: UUID
    checked_at: datetime

    model_config = {"from_attributes": True}


class AgentHealthReport(BaseModel):
    agent_name: str
    domain: str | None = None
    status: str = "healthy"
    tasks_completed: int = 0
    tasks_failed: int = 0
    avg_confidence: float | None = None
    detail: dict = Field(default_factory=dict)


class AgentHealthResponse(AgentHealthReport):
    id: UUID
    checked_at: datetime

    model_config = {"from_attributes": True}


class SystemOverview(BaseModel):
    total_services: int
    healthy_services: int
    degraded_services: int
    unhealthy_services: int
    total_agents: int
    healthy_agents: int
    services: list[ServiceHealthResponse]
    agents: list[AgentHealthResponse]
