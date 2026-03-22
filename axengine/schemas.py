"""AXEngine API schemas."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class GoalCreate(BaseModel):
    title: str
    description: str | None = None
    priority: int = 50
    created_by: str | None = None


class GoalResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    status: str
    priority: int
    created_by: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PlanResponse(BaseModel):
    id: UUID
    goal_id: UUID
    steps: list[dict]
    status: str
    current_step: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ExecutionLogResponse(BaseModel):
    id: UUID
    plan_id: UUID
    step_index: int
    agent_name: str | None
    action: str | None
    status: str
    confidence: float | None
    error_message: str | None
    started_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class OverrideRequest(BaseModel):
    execution_log_id: UUID
    original_action: dict
    override_action: dict
    reason: str
    overridden_by: str


class LLMRequest(BaseModel):
    prompt: str
    system: str = ""
    prefer_local: bool = True
    require_local: bool = False


class LLMResponse(BaseModel):
    response: str | None
    provider: str
    model: str
    error: str | None = None


class InterEngineTrigger(BaseModel):
    """Trigger from AXE_POE requesting AXEngine to act."""
    source: str = "axe_poe"
    trigger_type: str
    payload: dict = Field(default_factory=dict)
    priority: int = 50
