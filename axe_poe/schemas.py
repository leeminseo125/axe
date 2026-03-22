"""AXE_POE API schemas."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class WebhookEvent(BaseModel):
    source: str
    event_type: str
    payload: dict


class BatchCaptureRequest(BaseModel):
    source: str
    event_type: str
    events: list[dict]


class DataEventResponse(BaseModel):
    id: UUID
    source: str
    event_type: str
    normalized_payload: dict | None
    captured_at: datetime

    model_config = {"from_attributes": True}


class InsightResponse(BaseModel):
    id: UUID
    event_id: UUID | None
    insight_type: str
    severity: str
    summary: str
    detail: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class DecisionResponse(BaseModel):
    id: UUID
    insight_id: UUID | None
    recommended_action: str
    confidence: float
    status: str
    policy_check_result: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class ExecutionResponse(BaseModel):
    id: UUID
    decision_id: UUID | None
    action_type: str
    target_system: str | None
    status: str
    response_payload: dict
    executed_at: datetime | None
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class FeedbackCreate(BaseModel):
    execution_id: UUID
    metric_name: str
    metric_value: float
    feedback_type: str = "manual"
    detail: dict = Field(default_factory=dict)


class FeedbackResponse(BaseModel):
    id: UUID
    execution_id: UUID | None
    metric_name: str
    metric_value: float | None
    feedback_type: str
    recorded_at: datetime

    model_config = {"from_attributes": True}


class PipelineRunResult(BaseModel):
    events_captured: int
    insights_generated: int
    decisions_made: int
    executions_run: int
    feedbacks_recorded: int
