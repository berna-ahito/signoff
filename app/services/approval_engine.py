from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import ApprovalRule, PurchaseRequest
import logging

logger = logging.getLogger(__name__)

ALLOWED_TRANSITIONS = {
    "draft": ["pending_review"],
    "pending_review": ["pending_approval", "needs_rule"],
    "pending_approval": ["approved", "rejected", "needs_more_info"],
    "needs_rule": ["pending_approval"],
    "needs_more_info": ["draft"],
    "approved": [],
    "rejected": [],
}


def validate_transition(current_status: str, new_status: str) -> None:
    allowed = ALLOWED_TRANSITIONS.get(current_status, [])
    if new_status not in allowed:
        raise ValueError(f"Invalid transition: {current_status} -> {new_status}")


def evaluate_rules(rules: list, estimated_cost: float, category: str) -> Optional[object]:
    active = [r for r in rules if r.is_active]
    active.sort(key=lambda r: r.priority)
    for rule in active:
        if estimated_cost < rule.min_amount:
            continue
        if rule.max_amount is not None and estimated_cost > rule.max_amount:
            continue
        if rule.category is not None and rule.category.lower() != category.lower():
            continue
        return rule
    return None


def route_request(db: Session, request: PurchaseRequest) -> PurchaseRequest:
    rules = (
        db.query(ApprovalRule)
        .filter(ApprovalRule.is_active == True)
        .order_by(ApprovalRule.priority)
        .all()
    )
    match = evaluate_rules(rules, request.estimated_cost, request.category)
    if match:
        request.assigned_role = match.required_role
        request.status = "pending_approval"
    else:
        request.status = "needs_rule"
        request.assigned_role = None
    db.commit()
    db.refresh(request)
    return request


def apply_decision(db: Session, request: PurchaseRequest, decision: str, note: Optional[str]) -> PurchaseRequest:
    status_map = {
        "approved": "approved",
        "rejected": "rejected",
        "needs_more_info": "needs_more_info",
    }
    new_status = status_map.get(decision)
    if new_status is None:
        raise ValueError(f"Invalid decision value: {decision}")
    validate_transition(request.status, new_status)
    request.status = new_status
    db.commit()
    db.refresh(request)

    if decision in ("approved", "rejected"):
        logger.info(
            "Decision %s on request #%s: %s",
            decision.upper(),
            request.id,
            request.title,
        )

    return request
