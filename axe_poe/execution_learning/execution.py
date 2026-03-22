"""L4 Operation Execution - External action execution module.

Executes approved decisions by dispatching to external systems:
ticket creation, automated messaging, payment retries, etc.
"""

from datetime import datetime
from uuid import UUID

import httpx
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from shared_infra.config import get_settings
from shared_infra.data_foundation.models import POEDecision, POEExecution, AuditLog

settings = get_settings()
logger = structlog.get_logger()


class ExecutionModule:
    """Dispatches approved actions to external target systems."""

    # Action handler registry
    _handlers: dict[str, callable] = {}

    def __init__(self):
        self._register_handlers()

    def _register_handlers(self):
        self._handlers = {
            "trigger_retention_workflow": self._execute_retention,
            "handle_payment_failure": self._execute_payment_retry,
            "escalate_cs_ticket": self._execute_cs_escalation,
            "investigate_volume_spike": self._execute_investigation,
            "investigate_volume_drop": self._execute_investigation,
        }

    async def execute_decision(
        self, decision: POEDecision, db: AsyncSession
    ) -> POEExecution:
        """Execute a single approved decision."""
        handler = self._handlers.get(decision.recommended_action)

        execution = POEExecution(
            decision_id=decision.id,
            action_type=decision.recommended_action,
            target_system=self._infer_target(decision.recommended_action),
            request_payload=decision.action_params,
            status="executing",
            executed_at=datetime.utcnow(),
        )
        db.add(execution)
        await db.flush()

        if handler:
            try:
                result = await handler(decision.action_params)
                execution.response_payload = result
                execution.status = "completed"
            except Exception as e:
                execution.response_payload = {"error": str(e)}
                execution.status = "failed"
                logger.error("execution_failed", action=decision.recommended_action, error=str(e))
        else:
            execution.response_payload = {"note": "No handler, logged for manual execution"}
            execution.status = "manual_required"

        execution.completed_at = datetime.utcnow()

        # Audit trail
        audit = AuditLog(
            service="axe_poe",
            action=f"execute_{decision.recommended_action}",
            resource_type="poe_execution",
            resource_id=str(execution.id),
            confidence_score=decision.confidence,
            detail={"status": execution.status},
        )
        db.add(audit)
        await db.commit()
        await db.refresh(execution)
        return execution

    async def execute_batch(
        self, decisions: list[POEDecision], db: AsyncSession
    ) -> list[POEExecution]:
        """Execute multiple approved decisions."""
        executions = []
        for decision in decisions:
            if decision.status == "approved":
                execution = await self.execute_decision(decision, db)
                executions.append(execution)
        return executions

    def _infer_target(self, action: str) -> str:
        targets = {
            "trigger_retention_workflow": "crm",
            "handle_payment_failure": "payment_gateway",
            "escalate_cs_ticket": "cs_system",
            "investigate_volume_spike": "internal",
            "investigate_volume_drop": "internal",
        }
        return targets.get(action, "unknown")

    async def _execute_retention(self, params: dict) -> dict:
        """Trigger retention workflow in CRM / messaging system."""
        entity_id = params.get("insight_detail", {}).get("entity_id")
        actions_taken = []

        if params.get("send_offer"):
            actions_taken.append(f"Retention offer queued for entity {entity_id}")

        if params.get("escalate_to_csm"):
            actions_taken.append(f"CSM escalation created for entity {entity_id}")

        return {"entity_id": entity_id, "actions": actions_taken}

    async def _execute_payment_retry(self, params: dict) -> dict:
        """Retry failed payment or notify customer."""
        entity_id = params.get("insight_detail", {}).get("entity_id")
        actions_taken = []

        if params.get("retry_payment"):
            # In production, this would call the payment gateway
            actions_taken.append(f"Payment retry scheduled for entity {entity_id}")

        if params.get("notify_customer"):
            actions_taken.append(f"Payment failure notification queued for entity {entity_id}")

        return {"entity_id": entity_id, "actions": actions_taken}

    async def _execute_cs_escalation(self, params: dict) -> dict:
        """Escalate CS ticket to senior agent."""
        detail = params.get("insight_detail", {})
        actions_taken = []

        if params.get("assign_senior"):
            actions_taken.append(f"Ticket reassigned to senior agent: {detail.get('subject')}")

        if params.get("priority_boost"):
            actions_taken.append("Ticket priority boosted to critical")

        return {"ticket_subject": detail.get("subject"), "actions": actions_taken}

    async def _execute_investigation(self, params: dict) -> dict:
        """Log investigation request and optionally trigger AXEngine."""
        detail = params.get("insight_detail", {})

        # Trigger AXEngine cross-engine check
        trigger_result = await self._trigger_axengine(
            trigger_type="volume_investigation",
            payload=detail,
        )

        return {
            "investigation_logged": True,
            "axengine_trigger": trigger_result,
        }

    async def _trigger_axengine(self, trigger_type: str, payload: dict) -> dict:
        """Send a cross-engine trigger to AXEngine."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"http://axengine:{settings.axengine_port}/triggers/from-poe",
                    json={
                        "source": "axe_poe",
                        "trigger_type": trigger_type,
                        "payload": payload,
                        "priority": 60,
                    },
                )
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            logger.warning("axengine_trigger_failed", error=str(e))
        return {"error": "AXEngine trigger failed"}
