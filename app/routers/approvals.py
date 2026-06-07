from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.core.limiter import limiter
from app.db.base import get_db
from app.db.models import ApprovalDecision, ApprovalRule, PurchaseRequest, User
from app.schemas.approval import (
    ApprovalDecisionCreate,
    ApprovalDecisionResponse,
    ApprovalRuleCreate,
    ApprovalRuleResponse,
)
from app.services.approval_engine import apply_decision
from app.services.audit_service import ACTION_DECISION, log_action

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.post("/{request_id}/decide", response_model=ApprovalDecisionResponse)
@limiter.limit("20/minute")
def decide(
    request_id: int,
    request: Request,
    body: ApprovalDecisionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("manager", "finance", "admin")),
):
    req = db.get(PurchaseRequest, request_id)
    if req is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    if current_user.role != "admin" and req.assigned_role != current_user.role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the assigned approver")
    if req.status != "pending_approval":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request is not pending approval")
    old_status = req.status
    try:
        req = apply_decision(db, req, body.decision, body.note)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    decision_record = ApprovalDecision(
        request_id=req.id,
        actor_id=current_user.id,
        decision=body.decision,
        note=body.note,
    )
    db.add(decision_record)
    db.commit()
    db.refresh(decision_record)
    log_action(db, req.id, current_user.id, ACTION_DECISION, old_status, req.status, body.note)
    return ApprovalDecisionResponse.model_validate(decision_record)


@router.get("/rules", response_model=list[ApprovalRuleResponse])
def list_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    rules = db.query(ApprovalRule).order_by(ApprovalRule.priority).all()
    return [ApprovalRuleResponse.model_validate(r) for r in rules]


@router.post("/rules", response_model=ApprovalRuleResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def create_rule(
    request: Request,
    body: ApprovalRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    rule = ApprovalRule(
        name=body.name,
        min_amount=body.min_amount,
        max_amount=body.max_amount,
        category=body.category,
        required_role=body.required_role,
        priority=body.priority,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return ApprovalRuleResponse.model_validate(rule)
