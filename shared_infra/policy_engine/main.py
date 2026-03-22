"""Policy & Governance Engine - Authorization, approval workflows, and audit trails."""

from datetime import datetime
from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from shared_infra.database import get_db
from shared_infra.data_foundation.models import Policy, ApprovalWorkflow, AuditLog
from shared_infra.policy_engine.schemas import (
    PolicyCreate,
    PolicyResponse,
    PolicyCheckRequest,
    PolicyCheckResult,
    ApprovalRequest,
    ApprovalResponse,
    ApprovalDecision,
)

app = FastAPI(title="AXEworks Policy & Governance Engine", version="1.0.0")


@app.get("/health")
async def health():
    return {"service": "policy-engine", "status": "healthy", "version": "1.0.0"}


# ---- Policy CRUD ----

@app.post("/policies", response_model=PolicyResponse)
async def create_policy(body: PolicyCreate, db: AsyncSession = Depends(get_db)):
    policy = Policy(**body.model_dump())
    db.add(policy)
    await db.commit()
    await db.refresh(policy)
    return policy


@app.get("/policies", response_model=list[PolicyResponse])
async def list_policies(domain: str | None = None, db: AsyncSession = Depends(get_db)):
    query = select(Policy).where(Policy.is_active == True).order_by(Policy.priority)
    if domain:
        query = query.where(Policy.domain == domain)
    result = await db.execute(query)
    return result.scalars().all()


@app.get("/policies/{policy_id}", response_model=PolicyResponse)
async def get_policy(policy_id: UUID, db: AsyncSession = Depends(get_db)):
    policy = await db.get(Policy, policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


# ---- Policy Check (core gate for all engines) ----

@app.post("/policies/check", response_model=PolicyCheckResult)
async def check_policy(req: PolicyCheckRequest, db: AsyncSession = Depends(get_db)):
    """Evaluate whether an action is allowed under current policies.

    Rules engine: each policy has a list of rule objects with fields:
      - action_pattern (str): glob-style match on action_type
      - min_confidence (float): minimum confidence required for auto-execution
      - require_approval (bool): always require human approval
      - deny (bool): block the action entirely
    """
    query = (
        select(Policy)
        .where(Policy.is_active == True)
        .where(Policy.domain.in_([req.domain, "global"]))
        .order_by(Policy.priority)
    )
    result = await db.execute(query)
    policies = result.scalars().all()

    matched = []
    requires_approval = False
    denied = False
    reason = ""

    for policy in policies:
        for rule in policy.rules:
            pattern = rule.get("action_pattern", "*")
            if _match_pattern(pattern, req.action_type):
                matched.append(policy.name)

                if rule.get("deny"):
                    denied = True
                    reason = f"Denied by policy '{policy.name}'"
                    break

                min_conf = rule.get("min_confidence", 0.0)
                if req.confidence < min_conf:
                    requires_approval = True
                    reason = (
                        f"Confidence {req.confidence:.2f} below threshold "
                        f"{min_conf:.2f} in policy '{policy.name}'"
                    )

                if rule.get("require_approval"):
                    requires_approval = True
                    reason = f"Approval required by policy '{policy.name}'"

        if denied:
            break

    return PolicyCheckResult(
        allowed=not denied,
        requires_approval=requires_approval,
        matched_policies=matched,
        reason=reason,
    )


# ---- Approval Workflow ----

@app.post("/approvals", response_model=ApprovalResponse)
async def request_approval(body: ApprovalRequest, db: AsyncSession = Depends(get_db)):
    wf = ApprovalWorkflow(**body.model_dump())
    db.add(wf)
    await db.commit()
    await db.refresh(wf)
    return wf


@app.get("/approvals", response_model=list[ApprovalResponse])
async def list_approvals(status: str = "pending", db: AsyncSession = Depends(get_db)):
    query = (
        select(ApprovalWorkflow)
        .where(ApprovalWorkflow.status == status)
        .order_by(desc(ApprovalWorkflow.created_at))
    )
    result = await db.execute(query)
    return result.scalars().all()


@app.post("/approvals/{approval_id}/decide", response_model=ApprovalResponse)
async def decide_approval(
    approval_id: UUID,
    body: ApprovalDecision,
    db: AsyncSession = Depends(get_db),
):
    wf = await db.get(ApprovalWorkflow, approval_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Approval not found")
    if wf.status != "pending":
        raise HTTPException(status_code=400, detail="Approval already decided")

    wf.status = "approved" if body.approve else "rejected"
    wf.decided_by = body.decided_by
    wf.decided_at = datetime.utcnow()
    await db.commit()
    await db.refresh(wf)

    # Audit trail
    audit = AuditLog(
        service="policy-engine",
        action=f"approval_{wf.status}",
        actor=body.decided_by,
        resource_type="approval_workflow",
        resource_id=str(approval_id),
        detail={"reason": body.reason},
    )
    db.add(audit)
    await db.commit()

    return wf


def _match_pattern(pattern: str, value: str) -> bool:
    """Simple glob-style matching: * matches everything, prefix* matches prefix."""
    if pattern == "*":
        return True
    if pattern.endswith("*"):
        return value.startswith(pattern[:-1])
    return pattern == value
