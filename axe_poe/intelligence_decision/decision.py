"""L3 Operation Decision - Action recommendation and policy routing.

Takes insights from L2, selects optimal actions, checks them
against governance policies, and routes for execution.
"""

from uuid import UUID

import httpx
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from shared_infra.config import get_settings
from shared_infra.data_foundation.models import POEInsight, POEDecision

settings = get_settings()
logger = structlog.get_logger()


# Action playbook: maps insight types to recommended actions
ACTION_PLAYBOOK = {
    "volume_spike": {
        "action": "investigate_volume_spike",
        "params_template": {"notify_team": True, "auto_scale": False},
        "base_confidence": 0.75,
    },
    "volume_drop": {
        "action": "investigate_volume_drop",
        "params_template": {"check_upstream": True, "alert_oncall": True},
        "base_confidence": 0.70,
    },
    "churn_signal": {
        "action": "trigger_retention_workflow",
        "params_template": {"send_offer": True, "escalate_to_csm": True},
        "base_confidence": 0.80,
    },
    "payment_issue": {
        "action": "handle_payment_failure",
        "params_template": {"retry_payment": True, "notify_customer": True},
        "base_confidence": 0.85,
    },
    "cs_escalation": {
        "action": "escalate_cs_ticket",
        "params_template": {"assign_senior": True, "priority_boost": True},
        "base_confidence": 0.90,
    },
}


class DecisionEngine:
    """Recommends and gates actions based on insights and policies."""

    async def decide(
        self, insights: list[POEInsight], db: AsyncSession
    ) -> list[POEDecision]:
        """Generate decisions for a batch of insights."""
        decisions = []
        for insight in insights:
            decision = await self._decide_single(insight, db)
            if decision:
                decisions.append(decision)
        return decisions

    async def _decide_single(
        self, insight: POEInsight, db: AsyncSession
    ) -> POEDecision | None:
        playbook_entry = ACTION_PLAYBOOK.get(insight.insight_type)
        if not playbook_entry:
            logger.info("no_playbook", insight_type=insight.insight_type)
            return None

        # Build action params from template + insight detail
        params = {**playbook_entry["params_template"]}
        if insight.detail:
            params["insight_detail"] = insight.detail

        confidence = playbook_entry["base_confidence"]

        # Adjust confidence based on insight severity
        severity_boost = {"critical": 0.05, "high": 0.03, "warning": 0.0, "info": -0.05}
        confidence += severity_boost.get(insight.severity, 0.0)
        confidence = min(1.0, max(0.0, confidence))

        # Check against policy engine
        policy_result = await self._check_policy(
            playbook_entry["action"], insight.insight_type, confidence
        )

        status = "proposed"
        if not policy_result.get("allowed", True):
            status = "blocked"
        elif policy_result.get("requires_approval"):
            status = "awaiting_approval"
        elif confidence >= settings.confidence_threshold:
            status = "approved"

        decision = POEDecision(
            insight_id=insight.id,
            recommended_action=playbook_entry["action"],
            action_params=params,
            confidence=confidence,
            policy_check_result=policy_result,
            status=status,
        )
        db.add(decision)
        await db.commit()
        await db.refresh(decision)
        return decision

    async def _check_policy(
        self, action: str, domain: str, confidence: float
    ) -> dict:
        """Check action against the Policy Engine."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(
                    f"http://policy-engine:{settings.policy_engine_port}/policies/check",
                    json={
                        "action_type": action,
                        "domain": domain,
                        "confidence": confidence,
                    },
                )
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            logger.warning("policy_check_failed", error=str(e))

        # Default: allow but flag for review if confidence is low
        return {
            "allowed": True,
            "requires_approval": confidence < settings.confidence_threshold,
            "matched_policies": [],
            "reason": "Policy engine unreachable, using defaults",
        }
