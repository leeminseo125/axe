"""Pydantic schemas for Policy & Governance Engine."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class PolicyCreate(BaseModel):
    name: str
    description: str | None = None
    domain: str = "global"
    rules: list[dict] = Field(default_factory=list)
    priority: int = 100


class PolicyResponse(PolicyCreate):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PolicyCheckRequest(BaseModel):
    action_type: str
    domain: str = "global"
    context: dict = Field(default_factory=dict)
    confidence: float = 1.0


class PolicyCheckResult(BaseModel):
    allowed: bool
    requires_approval: bool = False
    matched_policies: list[str] = Field(default_factory=list)
    reason: str = ""


class ApprovalRequest(BaseModel):
    policy_id: UUID | None = None
    requested_by: str
    action_type: str
    payload: dict = Field(default_factory=dict)


class ApprovalResponse(BaseModel):
    id: UUID
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ApprovalDecision(BaseModel):
    decided_by: str
    approve: bool
    reason: str = ""
