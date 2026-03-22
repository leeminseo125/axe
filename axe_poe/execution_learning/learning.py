"""L5 Operation Learning - Feedback accumulation and model refinement.

Measures the effectiveness of executed actions, accumulates feedback,
and adjusts decision confidence scores and playbook weights over time.
"""

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from shared_infra.data_foundation.models import (
    POEExecution,
    POEDecision,
    POELearningFeedback,
)
from shared_infra.vector_store import upsert_vectors, search_vectors

import structlog

logger = structlog.get_logger()


class LearningLoop:
    """Accumulates execution feedback and refines future decisions."""

    async def record_feedback(
        self,
        execution_id: UUID,
        metric_name: str,
        metric_value: float,
        feedback_type: str = "auto",
        detail: dict | None = None,
        db: AsyncSession = None,
    ) -> POELearningFeedback:
        """Record a feedback metric for an execution."""
        feedback = POELearningFeedback(
            execution_id=execution_id,
            metric_name=metric_name,
            metric_value=metric_value,
            feedback_type=feedback_type,
            detail=detail or {},
        )
        db.add(feedback)
        await db.commit()
        await db.refresh(feedback)
        return feedback

    async def auto_evaluate_execution(
        self, execution: POEExecution, db: AsyncSession
    ) -> list[POELearningFeedback]:
        """Automatically evaluate an execution based on its outcome."""
        feedbacks = []

        # Completion metric
        success = 1.0 if execution.status == "completed" else 0.0
        fb = await self.record_feedback(
            execution.id, "completion_success", success, "auto",
            {"status": execution.status}, db,
        )
        feedbacks.append(fb)

        # Latency metric
        if execution.executed_at and execution.completed_at:
            latency = (execution.completed_at - execution.executed_at).total_seconds()
            fb = await self.record_feedback(
                execution.id, "execution_latency_seconds", latency, "auto", db=db,
            )
            feedbacks.append(fb)

        return feedbacks

    async def get_action_effectiveness(
        self, action_type: str, db: AsyncSession, window_days: int = 30
    ) -> dict:
        """Calculate effectiveness metrics for an action type over time."""
        cutoff = datetime.utcnow() - timedelta(days=window_days)

        # Get all executions for this action type
        exec_result = await db.execute(
            select(POEExecution)
            .where(POEExecution.action_type == action_type)
            .where(POEExecution.executed_at > cutoff)
        )
        executions = exec_result.scalars().all()

        if not executions:
            return {"action_type": action_type, "sample_size": 0}

        exec_ids = [e.id for e in executions]

        # Get feedback for these executions
        fb_result = await db.execute(
            select(POELearningFeedback)
            .where(POELearningFeedback.execution_id.in_(exec_ids))
        )
        feedbacks = fb_result.scalars().all()

        # Aggregate metrics
        metrics: dict[str, list[float]] = {}
        for fb in feedbacks:
            metrics.setdefault(fb.metric_name, []).append(fb.metric_value or 0)

        aggregated = {}
        for name, values in metrics.items():
            aggregated[name] = {
                "mean": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "count": len(values),
            }

        return {
            "action_type": action_type,
            "sample_size": len(executions),
            "success_rate": aggregated.get("completion_success", {}).get("mean", 0),
            "metrics": aggregated,
        }

    async def compute_confidence_adjustment(
        self, action_type: str, db: AsyncSession
    ) -> float:
        """Compute a confidence adjustment factor based on historical performance.

        Returns a value between -0.15 and +0.10 to adjust base confidence.
        """
        effectiveness = await self.get_action_effectiveness(action_type, db)
        success_rate = effectiveness.get("success_rate", 0.5)
        sample_size = effectiveness.get("sample_size", 0)

        if sample_size < 5:
            return 0.0  # Not enough data

        # High success rate -> slight confidence boost
        # Low success rate -> confidence penalty
        if success_rate >= 0.9:
            return min(0.10, (success_rate - 0.9) * 1.0)
        elif success_rate < 0.5:
            return max(-0.15, (success_rate - 0.5) * 0.3)

        return 0.0

    async def store_playbook_entry(
        self, action_type: str, context: str, outcome: str, embedding: list[float]
    ):
        """Store a successful execution pattern in the knowledge base for RAG."""
        from qdrant_client.models import PointStruct
        from uuid import uuid4

        point = PointStruct(
            id=str(uuid4()),
            vector=embedding,
            payload={
                "action_type": action_type,
                "context": context,
                "outcome": outcome,
                "stored_at": datetime.utcnow().isoformat(),
            },
        )
        upsert_vectors("poe_playbook", [point])

    async def search_similar_playbooks(
        self, query_embedding: list[float], limit: int = 5
    ) -> list[dict]:
        """Search for similar past executions in the knowledge base."""
        results = search_vectors("poe_playbook", query_embedding, limit=limit)
        return [
            {
                "action_type": r.payload.get("action_type"),
                "context": r.payload.get("context"),
                "outcome": r.payload.get("outcome"),
                "score": r.score,
            }
            for r in getattr(results, "points", [])
        ]
