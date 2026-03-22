"""Monitor - Anomaly detection and execution log analysis.

Watches execution logs for failures, low-confidence results,
and timing anomalies, then triggers re-planning or HITL escalation.
"""

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from shared_infra.config import get_settings
from shared_infra.data_foundation.models import ExecutionLog, ExecutionPlan

settings = get_settings()


class MonitorAlert:
    def __init__(self, alert_type: str, plan_id: UUID, step_index: int, detail: dict):
        self.alert_type = alert_type
        self.plan_id = plan_id
        self.step_index = step_index
        self.detail = detail
        self.timestamp = datetime.utcnow()


async def check_plan_health(plan: ExecutionPlan, db: AsyncSession) -> list[MonitorAlert]:
    """Inspect a plan's execution logs for anomalies."""
    alerts = []

    result = await db.execute(
        select(ExecutionLog).where(ExecutionLog.plan_id == plan.id)
    )
    logs = result.scalars().all()

    for log in logs:
        # Low confidence detection
        if log.confidence is not None and log.confidence < settings.confidence_threshold:
            alerts.append(MonitorAlert(
                alert_type="low_confidence",
                plan_id=plan.id,
                step_index=log.step_index,
                detail={
                    "confidence": log.confidence,
                    "threshold": settings.confidence_threshold,
                    "action": log.action,
                },
            ))

        # Failure detection
        if log.status == "failed":
            alerts.append(MonitorAlert(
                alert_type="step_failed",
                plan_id=plan.id,
                step_index=log.step_index,
                detail={"error": log.error_message, "action": log.action},
            ))

        # Long-running step detection (> 60s)
        if log.started_at and log.completed_at:
            duration = (log.completed_at - log.started_at).total_seconds()
            if duration > 60:
                alerts.append(MonitorAlert(
                    alert_type="slow_execution",
                    plan_id=plan.id,
                    step_index=log.step_index,
                    detail={"duration_seconds": duration, "action": log.action},
                ))

    return alerts


async def get_recent_failure_rate(db: AsyncSession, window_minutes: int = 60) -> float:
    """Calculate failure rate across all recent executions."""
    cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)

    total = await db.execute(
        select(func.count(ExecutionLog.id)).where(ExecutionLog.started_at > cutoff)
    )
    total_count = total.scalar() or 0

    failed = await db.execute(
        select(func.count(ExecutionLog.id))
        .where(ExecutionLog.started_at > cutoff)
        .where(ExecutionLog.status == "failed")
    )
    failed_count = failed.scalar() or 0

    if total_count == 0:
        return 0.0
    return failed_count / total_count
