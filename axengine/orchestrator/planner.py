"""Planner - Dynamically orders and schedules execution steps.

Takes parsed goal steps and produces an optimized execution plan,
respecting dependencies, parallelism opportunities, and resource constraints.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from shared_infra.data_foundation.models import Goal, ExecutionPlan
from axengine.orchestrator.goal_parser import ParsedGoal, ParsedStep


class PlanStep(dict):
    """Serializable plan step for JSONB storage."""
    pass


async def create_plan(parsed: ParsedGoal, goal_id: UUID, db: AsyncSession) -> ExecutionPlan:
    """Create an execution plan from parsed goal steps.

    Steps are topologically sorted by dependencies, with parallelizable
    groups identified for concurrent execution.
    """
    ordered = _topological_sort(parsed.steps)
    execution_groups = _group_parallel_steps(ordered)

    plan_steps = []
    for group_idx, group in enumerate(execution_groups):
        for step in group:
            plan_steps.append({
                "step_index": step.index,
                "group": group_idx,
                "action": step.action,
                "agent": step.agent,
                "params": step.params,
                "dependencies": step.dependencies,
                "estimated_confidence": step.estimated_confidence,
                "status": "pending",
            })

    plan = ExecutionPlan(
        goal_id=goal_id,
        steps=plan_steps,
        status="planned",
        current_step=0,
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


def _topological_sort(steps: list[ParsedStep]) -> list[ParsedStep]:
    """Sort steps respecting dependency ordering."""
    by_index = {s.index: s for s in steps}
    visited = set()
    result = []

    def visit(idx: int):
        if idx in visited:
            return
        visited.add(idx)
        step = by_index.get(idx)
        if step:
            for dep in step.dependencies:
                visit(dep)
            result.append(step)

    for s in steps:
        visit(s.index)

    return result


def _group_parallel_steps(ordered: list[ParsedStep]) -> list[list[ParsedStep]]:
    """Group steps that can execute in parallel (same dependency depth)."""
    if not ordered:
        return []

    depth_map: dict[int, int] = {}
    for step in ordered:
        if not step.dependencies:
            depth_map[step.index] = 0
        else:
            depth_map[step.index] = max(depth_map.get(d, 0) for d in step.dependencies) + 1

    max_depth = max(depth_map.values()) if depth_map else 0
    groups: list[list[ParsedStep]] = [[] for _ in range(max_depth + 1)]
    for step in ordered:
        groups[depth_map[step.index]].append(step)

    return groups
