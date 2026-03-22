"""AXE_POE - External Product AI Operations Engine.

Main FastAPI application implementing the Analyze-Decide-Execute-Learn
pipeline for external product operations:
  L1 Data Capture -> L2 Intelligence -> L3 Decision -> L4 Execution -> L5 Learning
"""

from datetime import datetime, timedelta
from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from shared_infra.database import get_db
from shared_infra.data_foundation.models import (
    POEDataEvent, POEInsight, POEDecision, POEExecution, POELearningFeedback,
)
from axe_poe.schemas import (
    WebhookEvent, BatchCaptureRequest, DataEventResponse,
    InsightResponse, DecisionResponse, ExecutionResponse,
    FeedbackCreate, FeedbackResponse, PipelineRunResult,
)
from axe_poe.data_capture.etl_pipeline import DataCaptureService
from axe_poe.intelligence_decision.intelligence import IntelligenceEngine
from axe_poe.intelligence_decision.decision import DecisionEngine
from axe_poe.execution_learning.execution import ExecutionModule
from axe_poe.execution_learning.learning import LearningLoop

app = FastAPI(title="AXE_POE - Product Operations Engine", version="1.0.0")

capture_service = DataCaptureService()
intelligence = IntelligenceEngine()
decision_engine = DecisionEngine()
execution_module = ExecutionModule()
learning_loop = LearningLoop()


# ---- Health ----

@app.get("/health")
async def health():
    return {"service": "axe-poe", "status": "healthy", "version": "1.0.0"}


# ---- L1: Data Capture ----

@app.post("/capture/webhook", response_model=DataEventResponse)
async def capture_webhook(body: WebhookEvent, db: AsyncSession = Depends(get_db)):
    """Ingest a single event from an external webhook."""
    event = await capture_service.ingest_webhook(body.source, body.event_type, body.payload, db)
    return event


@app.post("/capture/batch", response_model=list[DataEventResponse])
async def capture_batch(body: BatchCaptureRequest, db: AsyncSession = Depends(get_db)):
    """Ingest a batch of events."""
    events = await capture_service.capture_from_source(
        body.source, body.event_type, body.events, db
    )
    return events


@app.get("/events", response_model=list[DataEventResponse])
async def list_events(
    source: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    query = select(POEDataEvent).order_by(desc(POEDataEvent.captured_at)).limit(limit)
    if source:
        query = query.where(POEDataEvent.source == source)
    result = await db.execute(query)
    return result.scalars().all()


# ---- L2: Intelligence ----

@app.post("/analyze", response_model=list[InsightResponse])
async def run_analysis(window_minutes: int = 60, db: AsyncSession = Depends(get_db)):
    """Analyze recent events and generate insights."""
    insights = await intelligence.analyze_recent(db, window_minutes)
    return insights


@app.get("/insights", response_model=list[InsightResponse])
async def list_insights(
    severity: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    query = select(POEInsight).order_by(desc(POEInsight.created_at)).limit(limit)
    if severity:
        query = query.where(POEInsight.severity == severity)
    result = await db.execute(query)
    return result.scalars().all()


# ---- L3: Decision ----

@app.post("/decide", response_model=list[DecisionResponse])
async def run_decisions(db: AsyncSession = Depends(get_db)):
    """Generate decisions for all unprocessed insights."""
    # Get insights without decisions
    subq = select(POEDecision.insight_id)
    result = await db.execute(
        select(POEInsight)
        .where(POEInsight.id.notin_(subq))
        .order_by(desc(POEInsight.created_at))
        .limit(100)
    )
    insights = result.scalars().all()
    decisions = await decision_engine.decide(insights, db)
    return decisions


@app.get("/decisions", response_model=list[DecisionResponse])
async def list_decisions(
    status: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    query = select(POEDecision).order_by(desc(POEDecision.created_at)).limit(limit)
    if status:
        query = query.where(POEDecision.status == status)
    result = await db.execute(query)
    return result.scalars().all()


@app.post("/decisions/{decision_id}/approve", response_model=DecisionResponse)
async def approve_decision(decision_id: UUID, db: AsyncSession = Depends(get_db)):
    decision = await db.get(POEDecision, decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    decision.status = "approved"
    await db.commit()
    await db.refresh(decision)
    return decision


# ---- L4: Execution ----

@app.post("/execute", response_model=list[ExecutionResponse])
async def run_executions(db: AsyncSession = Depends(get_db)):
    """Execute all approved decisions."""
    result = await db.execute(
        select(POEDecision).where(POEDecision.status == "approved")
    )
    decisions = result.scalars().all()
    executions = await execution_module.execute_batch(decisions, db)
    return executions


@app.get("/executions", response_model=list[ExecutionResponse])
async def list_executions(
    status: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    query = select(POEExecution).order_by(desc(POEExecution.executed_at)).limit(limit)
    if status:
        query = query.where(POEExecution.status == status)
    result = await db.execute(query)
    return result.scalars().all()


# ---- L5: Learning ----

@app.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(body: FeedbackCreate, db: AsyncSession = Depends(get_db)):
    """Submit manual or external feedback for an execution."""
    fb = await learning_loop.record_feedback(
        body.execution_id, body.metric_name, body.metric_value,
        body.feedback_type, body.detail, db,
    )
    return fb


@app.get("/feedback", response_model=list[FeedbackResponse])
async def list_feedback(limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(POELearningFeedback)
        .order_by(desc(POELearningFeedback.recorded_at))
        .limit(limit)
    )
    return result.scalars().all()


@app.get("/learning/effectiveness/{action_type}")
async def action_effectiveness(action_type: str, db: AsyncSession = Depends(get_db)):
    return await learning_loop.get_action_effectiveness(action_type, db)


# ---- Full Pipeline Run ----

@app.post("/pipeline/run", response_model=PipelineRunResult)
async def run_full_pipeline(window_minutes: int = 60, db: AsyncSession = Depends(get_db)):
    """Execute the full L1->L5 pipeline in sequence.

    1. Analyze recent events (L2)
    2. Generate decisions (L3)
    3. Execute approved decisions (L4)
    4. Record auto-feedback (L5)
    """
    # L2: Analyze
    insights = await intelligence.analyze_recent(db, window_minutes)

    # L3: Decide
    decisions = await decision_engine.decide(insights, db)

    # L4: Execute approved decisions
    approved = [d for d in decisions if d.status == "approved"]
    executions = await execution_module.execute_batch(approved, db)

    # L5: Auto-evaluate
    feedbacks = []
    for execution in executions:
        fbs = await learning_loop.auto_evaluate_execution(execution, db)
        feedbacks.extend(fbs)

    return PipelineRunResult(
        events_captured=0,  # Events were already captured via webhooks
        insights_generated=len(insights),
        decisions_made=len(decisions),
        executions_run=len(executions),
        feedbacks_recorded=len(feedbacks),
    )


# ---- Dashboard Stats ----

@app.get("/stats")
async def poe_stats(db: AsyncSession = Depends(get_db)):
    """Aggregate stats for the Operator Cockpit."""
    from sqlalchemy import func

    events_24h = (await db.execute(
        select(func.count(POEDataEvent.id))
        .where(POEDataEvent.captured_at > datetime.utcnow() - timedelta(hours=24))
    )).scalar() or 0

    insights_24h = (await db.execute(
        select(func.count(POEInsight.id))
        .where(POEInsight.created_at > datetime.utcnow() - timedelta(hours=24))
    )).scalar() or 0

    pending_decisions = (await db.execute(
        select(func.count(POEDecision.id))
        .where(POEDecision.status.in_(["proposed", "awaiting_approval"]))
    )).scalar() or 0

    executions_24h = (await db.execute(
        select(func.count(POEExecution.id))
        .where(POEExecution.executed_at > datetime.utcnow() - timedelta(hours=24))
    )).scalar() or 0

    return {
        "events_24h": events_24h,
        "insights_24h": insights_24h,
        "pending_decisions": pending_decisions,
        "executions_24h": executions_24h,
    }
