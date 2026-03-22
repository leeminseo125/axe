"""AXEngine - Internal Operations AI Execution Engine.

Main FastAPI application providing:
- Goal-based orchestration (parse -> plan -> execute -> monitor -> replan)
- Human-in-the-Loop confidence gating
- Integration layer connector health
- LLM routing (local/cloud)
- Inter-engine trigger API (webhook from AXE_POE)
"""

from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from shared_infra.database import get_db
from shared_infra.data_foundation.models import Goal, ExecutionPlan, ExecutionLog
from axengine.schemas import (
    GoalCreate, GoalResponse, PlanResponse, ExecutionLogResponse,
    OverrideRequest, LLMRequest, LLMResponse, InterEngineTrigger,
)
from axengine.orchestrator.goal_parser import parse_goal_with_llm
from axengine.orchestrator.planner import create_plan
from axengine.orchestrator.executor import execute_plan
from axengine.orchestrator.monitor import check_plan_health, get_recent_failure_rate
from axengine.orchestrator.replanner import replan
from axengine.orchestrator.hitl import evaluate_confidence, record_override, get_override_stats
from axengine.integration_layer.connector_registry import ConnectorRegistry
from axengine.local_agent_bridge.llm_router import LLMRouter

llm_router = LLMRouter()
connector_registry = ConnectorRegistry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await connector_registry.close_all()


app = FastAPI(title="AXEngine - Internal Operations AI Engine", version="1.0.0", lifespan=lifespan)


# ---- Health ----

@app.get("/health")
async def health():
    providers = await llm_router.get_available_providers()
    return {
        "service": "axengine",
        "status": "healthy",
        "version": "1.0.0",
        "llm_providers": providers,
    }


# ---- Goal Orchestration ----

@app.post("/goals", response_model=GoalResponse)
async def create_goal(body: GoalCreate, db: AsyncSession = Depends(get_db)):
    goal = Goal(**body.model_dump())
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return goal


@app.get("/goals", response_model=list[GoalResponse])
async def list_goals(status: str | None = None, db: AsyncSession = Depends(get_db)):
    query = select(Goal).order_by(desc(Goal.created_at))
    if status:
        query = query.where(Goal.status == status)
    result = await db.execute(query)
    return result.scalars().all()


@app.post("/goals/{goal_id}/plan", response_model=PlanResponse)
async def plan_goal(goal_id: UUID, db: AsyncSession = Depends(get_db)):
    """Parse a goal and create an execution plan."""
    goal = await db.get(Goal, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    parsed = await parse_goal_with_llm(f"{goal.title}: {goal.description or ''}")
    plan = await create_plan(parsed, goal_id, db)

    goal.status = "planned"
    await db.commit()
    return plan


@app.post("/plans/{plan_id}/execute", response_model=list[ExecutionLogResponse])
async def execute(plan_id: UUID, db: AsyncSession = Depends(get_db)):
    """Execute a plan through the orchestrator pipeline."""
    plan = await db.get(ExecutionPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if plan.status not in ("planned", "replanned"):
        raise HTTPException(status_code=400, detail=f"Plan status is '{plan.status}', cannot execute")

    plan.status = "executing"
    await db.commit()

    logs = await execute_plan(plan, db)

    # Monitor phase
    alerts = await check_plan_health(plan, db)
    if alerts:
        new_plan = await replan(plan, alerts, db)
        if new_plan:
            plan.status = "superseded"
            await db.commit()

    return logs


@app.get("/plans/{plan_id}/monitor")
async def monitor_plan(plan_id: UUID, db: AsyncSession = Depends(get_db)):
    plan = await db.get(ExecutionPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    alerts = await check_plan_health(plan, db)
    return {
        "plan_id": str(plan_id),
        "plan_status": plan.status,
        "alerts": [
            {
                "type": a.alert_type,
                "step_index": a.step_index,
                "detail": a.detail,
            }
            for a in alerts
        ],
    }


# ---- Human-in-the-Loop ----

@app.post("/hitl/evaluate")
async def hitl_evaluate(confidence: float, action: str, db: AsyncSession = Depends(get_db)):
    decision = await evaluate_confidence(confidence, action, db)
    return {"confidence": confidence, "action": action, "decision": decision}


@app.post("/hitl/override")
async def hitl_override(body: OverrideRequest, db: AsyncSession = Depends(get_db)):
    override = await record_override(
        body.execution_log_id,
        body.original_action,
        body.override_action,
        body.reason,
        body.overridden_by,
        db,
    )
    return {"id": str(override.id), "status": "recorded"}


@app.get("/hitl/stats")
async def hitl_stats(db: AsyncSession = Depends(get_db)):
    return await get_override_stats(db)


# ---- Integration Layer ----

@app.get("/connectors")
async def list_connectors():
    return {"connectors": connector_registry.list_connectors()}


@app.get("/connectors/health")
async def connectors_health():
    return await connector_registry.health_check_all()


@app.get("/connectors/{name}/fetch")
async def fetch_connector_data(name: str, resource: str = "default"):
    connector = connector_registry.get(name)
    if not connector:
        raise HTTPException(status_code=404, detail=f"Connector '{name}' not found")
    records = await connector.fetch_records(resource=resource)
    return {"source": name, "count": len(records), "records": [r.model_dump() for r in records]}


# ---- LLM Router ----

@app.post("/llm/generate", response_model=LLMResponse)
async def llm_generate(body: LLMRequest):
    result = await llm_router.generate(
        body.prompt, system=body.system,
        prefer_local=body.prefer_local, require_local=body.require_local,
    )
    return LLMResponse(**result)


@app.get("/llm/providers")
async def llm_providers():
    providers = await llm_router.get_available_providers()
    return {"providers": providers}


# ---- Inter-Engine Trigger (from AXE_POE) ----

@app.post("/triggers/from-poe")
async def receive_poe_trigger(body: InterEngineTrigger, db: AsyncSession = Depends(get_db)):
    """Webhook endpoint for AXE_POE to trigger internal actions.

    Example: POE detects external anomaly -> triggers AXEngine to run internal check.
    """
    goal = Goal(
        title=f"[POE Trigger] {body.trigger_type}",
        description=f"Auto-generated from AXE_POE trigger: {body.payload}",
        priority=body.priority,
        created_by="axe_poe",
        status="pending",
    )
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return {"goal_id": str(goal.id), "status": "created", "trigger_type": body.trigger_type}


# ---- System Stats ----

@app.get("/stats")
async def system_stats(db: AsyncSession = Depends(get_db)):
    failure_rate = await get_recent_failure_rate(db)
    return {
        "failure_rate_1h": failure_rate,
        "connectors": connector_registry.list_connectors(),
        "llm_providers": await llm_router.get_available_providers(),
    }
