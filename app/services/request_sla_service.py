from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models import PurchaseRequest, User


def find_overdue_requests(db: Session, current_user: User):
    now = datetime.now(timezone.utc)
    q = (
        db.query(PurchaseRequest)
        .filter(PurchaseRequest.status == "pending_approval")
        .filter(PurchaseRequest.approval_due_at.isnot(None))
        .filter(PurchaseRequest.approval_due_at < now)
        .order_by(PurchaseRequest.approval_due_at.asc())
    )
    if current_user.role == "manager":
        q = q.filter(PurchaseRequest.assigned_role == "manager")
    elif current_user.role == "finance":
        q = q.filter(PurchaseRequest.assigned_role == "finance")
    return q
