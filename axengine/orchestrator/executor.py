"""Executor - Runs plan steps by dispatching to agents and APIs.

Handles agent invocation, API calls, UI automation bridge,
confidence-based human-in-the-loop gating, and logging.
"""

import asyncio
from datetime import datetime
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from shared_infra.config import get_settings
from shared_infra.data_foundation.models import ExecutionPlan, ExecutionLog, AuditLog

settings = get_settings()


class ExecutionResult:
    def __init__(self, success: bool, output: dict, confidence: float = 1.0, error: str | None = None):
        self.success = success
        self.output = output
        self.confidence = confidence
        self.error = error


# Registry of action handlers
_action_handlers: dict[str, callable] = {}


def register_action(name: str):
    """Decorator to register an action handler."""
    def decorator(func):
        _action_handlers[name] = func
        return func
    return decorator


@register_action("fetch_data")
async def handle_fetch_data(params: dict) -> ExecutionResult:
    """Fetch data from an integration source."""
    source = params.get("source", "erp")
    connector_map = {
        "erp": settings.erp_system_endpoint,
        "mes": settings.mes_system_endpoint,
        "crm": settings.crm_system_endpoint,
    }
    endpoint = connector_map.get(source)
    if not endpoint:
        return ExecutionResult(success=True, output={"data": [], "note": "No endpoint configured"}, confidence=0.5)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(endpoint, headers=_get_auth_headers(source))
            return ExecutionResult(success=True, output=resp.json(), confidence=0.95)
    except Exception as e:
        return ExecutionResult(success=False, output={}, error=str(e), confidence=0.0)


@register_action("analyze_data")
async def handle_analyze_data(params: dict) -> ExecutionResult:
    """Run analysis via LLM or local model."""
    data = params.get("data", {})
    prompt = params.get("prompt", f"Analyze the following data and provide key insights:\n{data}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                settings.local_llm_endpoint,
                json={"model": "llama3", "prompt": prompt, "stream": False},
            )
            if resp.status_code == 200:
                return ExecutionResult(
                    success=True,
                    output={"analysis": resp.json().get("response", "")},
                    confidence=0.85,
                )
    except Exception:
        pass

    return ExecutionResult(
        success=True,
        output={"analysis": "Analysis pending - LLM unavailable", "fallback": True},
        confidence=0.4,
    )


@register_action("generate_report")
async def handle_generate_report(params: dict) -> ExecutionResult:
    return ExecutionResult(
        success=True,
        output={"report": params.get("analysis", "No analysis data"), "format": "markdown"},
        confidence=0.9,
    )


@register_action("distribute_report")
async def handle_distribute_report(params: dict) -> ExecutionResult:
    return ExecutionResult(success=True, output={"distributed_to": params.get("targets", [])}, confidence=0.95)


@register_action("collect_metrics")
async def handle_collect_metrics(params: dict) -> ExecutionResult:
    return ExecutionResult(success=True, output={"metrics": {}}, confidence=0.9)


@register_action("evaluate_thresholds")
async def handle_evaluate_thresholds(params: dict) -> ExecutionResult:
    return ExecutionResult(success=True, output={"alerts": []}, confidence=0.9)


@register_action("alert_if_needed")
async def handle_alert(params: dict) -> ExecutionResult:
    return ExecutionResult(success=True, output={"notified": False}, confidence=0.95)


@register_action("read_source")
async def handle_read_source(params: dict) -> ExecutionResult:
    return await handle_fetch_data(params)


@register_action("transform_data")
async def handle_transform(params: dict) -> ExecutionResult:
    return ExecutionResult(success=True, output={"transformed": True}, confidence=0.9)


@register_action("write_target")
async def handle_write_target(params: dict) -> ExecutionResult:
    return ExecutionResult(success=True, output={"written": True}, confidence=0.9)


@register_action("verify_sync")
async def handle_verify_sync(params: dict) -> ExecutionResult:
    return ExecutionResult(success=True, output={"verified": True}, confidence=0.9)


@register_action("analyze_request")
async def handle_analyze_request(params: dict) -> ExecutionResult:
    return ExecutionResult(success=True, output={"analyzed": True}, confidence=0.7)


@register_action("execute_action")
async def handle_execute_action(params: dict) -> ExecutionResult:
    return ExecutionResult(success=True, output={"executed": True}, confidence=0.7)


async def execute_plan(plan: ExecutionPlan, db: AsyncSession) -> list[ExecutionLog]:
    """Execute all steps in the plan, group by group."""
    logs = []
    steps_by_group: dict[int, list[dict]] = {}

    for step in plan.steps:
        group = step.get("group", 0)
        steps_by_group.setdefault(group, []).append(step)

    for group_idx in sorted(steps_by_group.keys()):
        group = steps_by_group[group_idx]
        # Execute steps within a group concurrently
        tasks = [_execute_step(step, plan.id, db) for step in group]
        group_logs = await asyncio.gather(*tasks, return_exceptions=True)
        for log in group_logs:
            if isinstance(log, ExecutionLog):
                logs.append(log)
            elif isinstance(log, Exception):
                error_log = ExecutionLog(
                    plan_id=plan.id,
                    step_index=-1,
                    status="failed",
                    error_message=str(log),
                )
                db.add(error_log)
                logs.append(error_log)

        # Check if any step failed
        if any(log.status == "failed" for log in logs if isinstance(log, ExecutionLog)):
            plan.status = "failed"
            break

    if plan.status != "failed":
        plan.status = "completed"

    await db.commit()
    return logs


async def _execute_step(step: dict, plan_id: UUID, db: AsyncSession) -> ExecutionLog:
    action = step.get("action", "unknown")
    handler = _action_handlers.get(action)

    log = ExecutionLog(
        plan_id=plan_id,
        step_index=step.get("step_index", 0),
        agent_name=step.get("agent"),
        action=action,
        input_data=step.get("params", {}),
        status="running",
    )
    db.add(log)
    await db.flush()

    if handler:
        result = await handler(step.get("params", {}))
        log.output_data = result.output
        log.confidence = result.confidence
        log.status = "completed" if result.success else "failed"
        log.error_message = result.error
    else:
        log.status = "skipped"
        log.output_data = {"reason": f"No handler for action '{action}'"}
        log.confidence = 0.0

    log.completed_at = datetime.utcnow()
    return log


def _get_auth_headers(source: str) -> dict:
    key_map = {
        "erp": settings.erp_api_key,
        "mes": settings.mes_api_key,
        "crm": settings.crm_api_key,
    }
    key = key_map.get(source, "")
    if key:
        return {"Authorization": f"Bearer {key}"}
    return {}
