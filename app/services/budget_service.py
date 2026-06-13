from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import Department, PurchaseRequest

PENDING_BUDGET_STATUSES = ("pending_review", "pending_approval", "needs_rule", "needs_more_info")


def month_bounds(now: Optional[datetime] = None) -> tuple[datetime, datetime]:
    current = now or datetime.now(timezone.utc)
    start = current.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return start, end


def budget_summary(db: Session, department: Department) -> dict:
    start, end = month_bounds()
    base = (
        db.query(func.coalesce(func.sum(PurchaseRequest.estimated_cost), 0.0))
        .filter(PurchaseRequest.department_id == department.id)
        .filter(PurchaseRequest.created_at >= start)
        .filter(PurchaseRequest.created_at < end)
    )
    approved = base.filter(PurchaseRequest.status == "approved").scalar() or 0.0
    pending = base.filter(PurchaseRequest.status.in_(PENDING_BUDGET_STATUSES)).scalar() or 0.0
    remaining = float(department.monthly_budget or 0.0) - float(approved) - float(pending)
    return {
        "department_id": department.id,
        "monthly_budget": float(department.monthly_budget or 0.0),
        "approved_spend_this_month": float(approved),
        "pending_spend_this_month": float(pending),
        "remaining_budget": remaining,
        "over_budget": remaining < 0,
    }


def would_exceed_budget(db: Session, request: PurchaseRequest) -> Optional[str]:
    if request.department_id is None:
        return None
    department = db.get(Department, request.department_id)
    if department is None:
        return None
    summary = budget_summary(db, department)
    projected = summary["approved_spend_this_month"] + summary["pending_spend_this_month"] + request.estimated_cost
    if projected <= summary["monthly_budget"]:
        return None
    return (
        f"Request would exceed {department.name} monthly budget "
        f"({projected:.2f} projected vs {summary['monthly_budget']:.2f} budget)."
    )
