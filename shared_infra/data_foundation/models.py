"""SQLAlchemy ORM models mirroring the init.sql schema."""

import uuid
from datetime import datetime
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared_infra.database import Base


# ---- Audit ----
class AuditLog(Base):
    __tablename__ = "ax_audit_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    service: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(128))
    actor: Mapped[str | None] = mapped_column(String(128))
    resource_type: Mapped[str | None] = mapped_column(String(64))
    resource_id: Mapped[str | None] = mapped_column(String(256))
    detail: Mapped[dict] = mapped_column(JSONB, default=dict)
    confidence_score: Mapped[float | None] = mapped_column(Float)
    outcome: Mapped[str] = mapped_column(String(32), default="success")


# ---- Policy ----
class Policy(Base):
    __tablename__ = "ax_policies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(256), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    domain: Mapped[str] = mapped_column(String(64), default="global")
    rules: Mapped[list] = mapped_column(JSONB, default=list)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ApprovalWorkflow(Base):
    __tablename__ = "ax_approval_workflows"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("ax_policies.id"))
    requested_by: Mapped[str] = mapped_column(String(128))
    action_type: Mapped[str] = mapped_column(String(128))
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    decided_by: Mapped[str | None] = mapped_column(String(128))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


# ---- Goals & Execution ----
class Goal(Base):
    __tablename__ = "ax_goals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    priority: Mapped[int] = mapped_column(Integer, default=50)
    created_by: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    plans: Mapped[list["ExecutionPlan"]] = relationship(back_populates="goal", cascade="all, delete-orphan")


class ExecutionPlan(Base):
    __tablename__ = "ax_execution_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    goal_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ax_goals.id", ondelete="CASCADE"))
    steps: Mapped[list] = mapped_column(JSONB, default=list)
    status: Mapped[str] = mapped_column(String(32), default="planned")
    current_step: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    goal: Mapped["Goal"] = relationship(back_populates="plans")
    logs: Mapped[list["ExecutionLog"]] = relationship(back_populates="plan", cascade="all, delete-orphan")


class ExecutionLog(Base):
    __tablename__ = "ax_execution_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ax_execution_plans.id", ondelete="CASCADE"))
    step_index: Mapped[int] = mapped_column(Integer)
    agent_name: Mapped[str | None] = mapped_column(String(128))
    action: Mapped[str | None] = mapped_column(String(256))
    input_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    output_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="running")
    confidence: Mapped[float | None] = mapped_column(Float)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    plan: Mapped["ExecutionPlan"] = relationship(back_populates="logs")


class HITLOverride(Base):
    __tablename__ = "ax_hitl_overrides"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_log_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("ax_execution_logs.id"))
    original_action: Mapped[dict] = mapped_column(JSONB)
    override_action: Mapped[dict] = mapped_column(JSONB)
    reason: Mapped[str | None] = mapped_column(Text)
    overridden_by: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


# ---- POE Pipeline ----
class POEDataEvent(Base):
    __tablename__ = "ax_poe_data_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(128))
    event_type: Mapped[str] = mapped_column(String(128))
    raw_payload: Mapped[dict] = mapped_column(JSONB)
    normalized_payload: Mapped[dict | None] = mapped_column(JSONB)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class POEInsight(Base):
    __tablename__ = "ax_poe_insights"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("ax_poe_data_events.id"))
    insight_type: Mapped[str] = mapped_column(String(128))
    severity: Mapped[str] = mapped_column(String(32), default="info")
    summary: Mapped[str] = mapped_column(Text)
    detail: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class POEDecision(Base):
    __tablename__ = "ax_poe_decisions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    insight_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("ax_poe_insights.id"))
    recommended_action: Mapped[str] = mapped_column(String(256))
    action_params: Mapped[dict] = mapped_column(JSONB, default=dict)
    confidence: Mapped[float] = mapped_column(Float)
    policy_check_result: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="proposed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class POEExecution(Base):
    __tablename__ = "ax_poe_executions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    decision_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("ax_poe_decisions.id"))
    action_type: Mapped[str] = mapped_column(String(128))
    target_system: Mapped[str | None] = mapped_column(String(128))
    request_payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    response_payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class POELearningFeedback(Base):
    __tablename__ = "ax_poe_learning_feedback"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("ax_poe_executions.id"))
    metric_name: Mapped[str] = mapped_column(String(128))
    metric_value: Mapped[float | None] = mapped_column(Float)
    feedback_type: Mapped[str] = mapped_column(String(64), default="auto")
    detail: Mapped[dict] = mapped_column(JSONB, default=dict)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


# ---- poQat Health ----
class ServiceHealth(Base):
    __tablename__ = "ax_service_health"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_name: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="healthy")
    latency_ms: Mapped[float | None] = mapped_column(Float)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    detail: Mapped[dict] = mapped_column(JSONB, default=dict)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class AgentHealth(Base):
    __tablename__ = "ax_agent_health"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name: Mapped[str] = mapped_column(String(128))
    domain: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="healthy")
    tasks_completed: Mapped[int] = mapped_column(Integer, default=0)
    tasks_failed: Mapped[int] = mapped_column(Integer, default=0)
    avg_confidence: Mapped[float | None] = mapped_column(Float)
    detail: Mapped[dict] = mapped_column(JSONB, default=dict)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
