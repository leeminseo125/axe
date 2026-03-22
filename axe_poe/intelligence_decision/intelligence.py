"""L2 Operation Intelligence - Anomaly detection and business interpretation.

Analyzes captured events to detect anomalies, predict churn,
identify trends, and generate actionable insights.
"""

from datetime import datetime, timedelta
from uuid import UUID

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from shared_infra.data_foundation.models import POEDataEvent, POEInsight

import structlog

logger = structlog.get_logger()


class IntelligenceEngine:
    """Transforms raw events into business insights."""

    async def analyze_events(
        self, events: list[POEDataEvent], db: AsyncSession
    ) -> list[POEInsight]:
        """Run all analysis modules on a batch of events."""
        insights = []

        # Run detection modules
        for detector in [
            self._detect_volume_anomaly,
            self._detect_churn_signals,
            self._detect_payment_issues,
            self._detect_cs_escalation,
        ]:
            batch_insights = await detector(events, db)
            insights.extend(batch_insights)

        return insights

    async def analyze_recent(
        self, db: AsyncSession, window_minutes: int = 60
    ) -> list[POEInsight]:
        """Analyze events from the last N minutes."""
        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
        result = await db.execute(
            select(POEDataEvent).where(POEDataEvent.captured_at > cutoff)
        )
        events = result.scalars().all()
        if not events:
            return []
        return await self.analyze_events(events, db)

    async def _detect_volume_anomaly(
        self, events: list[POEDataEvent], db: AsyncSession
    ) -> list[POEInsight]:
        """Detect unusual spikes or drops in event volume by source."""
        insights = []
        by_source: dict[str, int] = {}
        for e in events:
            by_source[e.source] = by_source.get(e.source, 0) + 1

        # Compare against historical average (last 24h in 1h windows)
        for source, count in by_source.items():
            historical = await self._get_historical_avg(source, db)
            if historical > 0:
                ratio = count / historical
                if ratio > 2.0:
                    insight = POEInsight(
                        insight_type="volume_spike",
                        severity="warning",
                        summary=f"Event volume for '{source}' is {ratio:.1f}x above average",
                        detail={"source": source, "current": count, "average": historical, "ratio": ratio},
                    )
                    db.add(insight)
                    insights.append(insight)
                elif ratio < 0.3:
                    insight = POEInsight(
                        insight_type="volume_drop",
                        severity="warning",
                        summary=f"Event volume for '{source}' dropped to {ratio:.1f}x of average",
                        detail={"source": source, "current": count, "average": historical, "ratio": ratio},
                    )
                    db.add(insight)
                    insights.append(insight)

        if insights:
            await db.commit()
        return insights

    async def _detect_churn_signals(
        self, events: list[POEDataEvent], db: AsyncSession
    ) -> list[POEInsight]:
        """Detect potential churn indicators from user behavior."""
        insights = []
        churn_keywords = {"cancel", "unsubscribe", "downgrade", "delete_account", "churn"}

        for event in events:
            normalized = event.normalized_payload or {}
            action = str(normalized.get("action", "")).lower()
            event_type = event.event_type.lower()

            if any(kw in action or kw in event_type for kw in churn_keywords):
                entity_id = normalized.get("entity_id")
                insight = POEInsight(
                    event_id=event.id,
                    insight_type="churn_signal",
                    severity="high",
                    summary=f"Churn signal detected for entity {entity_id}: {action or event_type}",
                    detail={
                        "entity_id": entity_id,
                        "signal": action or event_type,
                        "source": event.source,
                    },
                )
                db.add(insight)
                insights.append(insight)

        if insights:
            await db.commit()
        return insights

    async def _detect_payment_issues(
        self, events: list[POEDataEvent], db: AsyncSession
    ) -> list[POEInsight]:
        """Detect payment failures and refund patterns."""
        insights = []
        failure_keywords = {"failed", "declined", "error", "refund", "chargeback"}

        for event in events:
            if event.source != "payments":
                continue
            normalized = event.normalized_payload or {}
            status = str(normalized.get("status", "")).lower()

            if any(kw in status for kw in failure_keywords):
                insight = POEInsight(
                    event_id=event.id,
                    insight_type="payment_issue",
                    severity="high",
                    summary=f"Payment issue: {status} for amount {normalized.get('amount')}",
                    detail={
                        "entity_id": normalized.get("entity_id"),
                        "amount": normalized.get("amount"),
                        "status": status,
                    },
                )
                db.add(insight)
                insights.append(insight)

        if insights:
            await db.commit()
        return insights

    async def _detect_cs_escalation(
        self, events: list[POEDataEvent], db: AsyncSession
    ) -> list[POEInsight]:
        """Detect CS ticket patterns that need escalation."""
        insights = []
        high_priority = {"urgent", "critical", "high"}

        for event in events:
            if event.source != "cs_tickets":
                continue
            normalized = event.normalized_payload or {}
            priority = str(normalized.get("priority", "")).lower()

            if priority in high_priority:
                insight = POEInsight(
                    event_id=event.id,
                    insight_type="cs_escalation",
                    severity="high",
                    summary=f"High-priority CS ticket: {normalized.get('subject', 'N/A')}",
                    detail={
                        "entity_id": normalized.get("entity_id"),
                        "subject": normalized.get("subject"),
                        "priority": priority,
                    },
                )
                db.add(insight)
                insights.append(insight)

        if insights:
            await db.commit()
        return insights

    async def _get_historical_avg(self, source: str, db: AsyncSession) -> float:
        """Get average hourly event count for a source over the last 24 hours."""
        cutoff = datetime.utcnow() - timedelta(hours=24)
        result = await db.execute(
            select(func.count(POEDataEvent.id))
            .where(POEDataEvent.source == source)
            .where(POEDataEvent.captured_at > cutoff)
        )
        total = result.scalar() or 0
        return total / 24.0
