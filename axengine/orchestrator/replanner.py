"""Re-Planner - Generates alternative execution paths on failure.

When the Monitor detects step failures or low-confidence results,
the Re-Planner constructs an alternative path to achieve the goal.
"""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from shared_infra.data_foundation.models import ExecutionPlan, ExecutionLog, Goal
from axengine.orchestrator.monitor import MonitorAlert
from axengine.orchestrator.goal_parser import ParsedStep


ALTERNATIVE_ACTIONS = {
    "fetch_data": ["fetch_data_cached", "fetch_data_fallback", "manual_data_entry"],
    "analyze_data": ["analyze_data_simple", "analyze_data_rule_based"],
    "generate_report": ["generate_report_basic"],
    "distribute_report": ["distribute_report_email"],
}


async def replan(
    plan: ExecutionPlan,
    alerts: list[MonitorAlert],
    db: AsyncSession,
) -> ExecutionPlan | None:
    """Create an alternative plan based on detected issues.

    Strategy:
    1. For failed steps, substitute with alternative actions if available.
    2. For low-confidence steps, wrap with verification step.
    3. If no alternatives exist, mark plan as needing human intervention.
    """
    failed_indices = {a.step_index for a in alerts if a.alert_type == "step_failed"}
    low_conf_indices = {a.step_index for a in alerts if a.alert_type == "low_confidence"}

    new_steps = []
    modified = False

    for step in plan.steps:
        idx = step.get("step_index", 0)

        if idx in failed_indices:
            original_action = step.get("action", "")
            alternatives = ALTERNATIVE_ACTIONS.get(original_action, [])

            if alternatives:
                alt_action = alternatives[0]
                new_step = {**step, "action": alt_action, "status": "pending"}
                new_step["params"] = {**step.get("params", {}), "_replan_reason": "step_failed"}
                new_steps.append(new_step)
                modified = True
            else:
                new_step = {**step, "status": "needs_human_review"}
                new_steps.append(new_step)
                modified = True

        elif idx in low_conf_indices:
            new_steps.append({**step, "status": "pending"})
            # Add verification step after low-confidence step
            verify_step = {
                "step_index": len(plan.steps) + len(new_steps),
                "group": step.get("group", 0) + 1,
                "action": "verify_output",
                "agent": "validation_agent",
                "params": {"verify_step_index": idx},
                "dependencies": [idx],
                "status": "pending",
            }
            new_steps.append(verify_step)
            modified = True
        else:
            new_steps.append(step)

    if not modified:
        return None

    new_plan = ExecutionPlan(
        goal_id=plan.goal_id,
        steps=new_steps,
        status="replanned",
        current_step=0,
    )
    db.add(new_plan)
    await db.commit()
    await db.refresh(new_plan)
    return new_plan
