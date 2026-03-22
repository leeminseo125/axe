"""Human-in-the-Loop (HITL) - Confidence-based routing and override tracking.

Routes decisions to human operators when confidence is below threshold.
Tracks overrides and adjusts thresholds over time based on accumulated data.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from shared_infra.config import get_settings
from shared_infra.data_foundation.models import (
    ExecutionLog,
    HITLOverride,
    AuditLog,
)

settings = get_settings()


class HITLDecision:
    AUTO_EXECUTE = "auto_execute"
    NEEDS_REVIEW = "needs_review"
    BLOCKED = "blocked"


async def evaluate_confidence(
    confidence: float,
    action: str,
    db: AsyncSession,
) -> str:
    """Determine execution mode based on confidence and dynamic threshold.

    - >= threshold: auto-execute
    - >= threshold - 0.15: needs human review
    - below that: blocked
    """
    threshold = await _get_dynamic_threshold(action, db)

    if confidence >= threshold:
        return HITLDecision.AUTO_EXECUTE
    elif confidence >= threshold - 0.15:
        return HITLDecision.NEEDS_REVIEW
    else:
        return HITLDecision.BLOCKED


async def record_override(
    execution_log_id: UUID,
    original_action: dict,
    override_action: dict,
    reason: str,
    overridden_by: str,
    db: AsyncSession,
) -> HITLOverride:
    """Record a human override of an AI decision."""
    override = HITLOverride(
        execution_log_id=execution_log_id,
        original_action=original_action,
        override_action=override_action,
        reason=reason,
        overridden_by=overridden_by,
    )
    db.add(override)

    # Audit trail
    audit = AuditLog(
        service="axengine",
        action="hitl_override",
        actor=overridden_by,
        resource_type="execution_log",
        resource_id=str(execution_log_id),
        detail={
            "original": original_action,
            "override": override_action,
            "reason": reason,
        },
    )
    db.add(audit)
    await db.commit()
    await db.refresh(override)
    return override


async def _get_dynamic_threshold(action: str, db: AsyncSession) -> float:
    """Adjust confidence threshold based on historical override patterns.

    If humans frequently override a particular action type, lower the
    auto-execution threshold (require more human review).
    If overrides are rare, the default threshold stands.
    """
    base_threshold = settings.confidence_threshold

    # Count recent overrides for this action type
    result = await db.execute(
        select(func.count(HITLOverride.id))
        .join(ExecutionLog, HITLOverride.execution_log_id == ExecutionLog.id)
        .where(ExecutionLog.action == action)
    )
    override_count = result.scalar() or 0

    # Count total executions for this action
    result = await db.execute(
        select(func.count(ExecutionLog.id)).where(ExecutionLog.action == action)
    )
    total_count = result.scalar() or 0

    if total_count < 10:
        return base_threshold

    override_rate = override_count / total_count

    # If override rate > 20%, raise threshold by up to 0.10
    # If override rate < 5%, lower threshold by up to 0.05
    if override_rate > 0.20:
        adjustment = min(0.10, override_rate * 0.5)
        return min(0.99, base_threshold + adjustment)
    elif override_rate < 0.05:
        adjustment = min(0.05, (0.05 - override_rate) * 0.5)
        return max(0.50, base_threshold - adjustment)

    return base_threshold


async def get_override_stats(db: AsyncSession) -> dict:
    """Get aggregate override statistics for dashboard."""
    total = await db.execute(select(func.count(HITLOverride.id)))
    total_count = total.scalar() or 0

    # Overrides by action type
    result = await db.execute(
        select(ExecutionLog.action, func.count(HITLOverride.id))
        .join(ExecutionLog, HITLOverride.execution_log_id == ExecutionLog.id)
        .group_by(ExecutionLog.action)
    )
    by_action = {row[0]: row[1] for row in result.all()}

    return {
        "total_overrides": total_count,
        "by_action": by_action,
        "current_base_threshold": settings.confidence_threshold,
    }
