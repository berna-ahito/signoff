from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user, get_db
from app.db.models import PurchaseRequest, User
from app.schemas.analytics import CategorySummary, SpendGroup

router = APIRouter(prefix="/analytics", tags=["analytics"])

_VALID_GROUP_BY = {"category", "urgency", "status"}

_GROUP_BY_FIELDS = {
    "category": PurchaseRequest.category,
    "urgency": PurchaseRequest.urgency,
    "status": PurchaseRequest.status,
}

_PENDING_STATUSES = [
    "draft",
    "submitted",
    "pending_review",
    "pending_approval",
    "needs_rule",
    "needs_more_info",
]


def _scope_to_user(query, current_user: User):
    if current_user.role == "admin":
        return query
    if current_user.role == "requester":
        return query.filter(PurchaseRequest.requester_id == current_user.id)
    if current_user.role in ("manager", "finance"):
        return query.filter(
            or_(
                PurchaseRequest.assigned_role == current_user.role,
                PurchaseRequest.requester_id == current_user.id,
            )
        )
    return query.filter(PurchaseRequest.requester_id == current_user.id)


@router.get("/spend", response_model=list[SpendGroup])
def get_spend(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    group_by: str = Query("category"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[SpendGroup]:
    if group_by not in _VALID_GROUP_BY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"group_by must be one of: {', '.join(sorted(_VALID_GROUP_BY))}",
        )

    # Parse optional date filters
    dt_from: Optional[datetime] = None
    dt_to: Optional[datetime] = None

    if date_from is not None:
        try:
            dt_from = datetime.strptime(date_from, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid date_from format. Expected YYYY-MM-DD, got: {date_from!r}",
            )

    if date_to is not None:
        try:
            dt_to = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid date_to format. Expected YYYY-MM-DD, got: {date_to!r}",
            )

    group_field = _GROUP_BY_FIELDS[group_by]

    query = _scope_to_user(
        db.query(
            group_field.label("group"),
            func.count(PurchaseRequest.id).label("count"),
            func.coalesce(func.sum(PurchaseRequest.estimated_cost), 0.0).label("total"),
        )
        .filter(PurchaseRequest.status == "approved"),
        current_user,
    )

    if dt_from is not None:
        query = query.filter(PurchaseRequest.created_at >= dt_from)
    if dt_to is not None:
        query = query.filter(PurchaseRequest.created_at < dt_to)

    rows = query.group_by(group_field).order_by(func.sum(PurchaseRequest.estimated_cost).desc()).all()

    return [
        SpendGroup(group=row.group, count=row.count, total_estimated_cost=row.total)
        for row in rows
    ]


@router.get("/categories", response_model=list[CategorySummary])
def get_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[CategorySummary]:
    # Query 1: approved counts/totals per category
    approved_rows = _scope_to_user(
        db.query(
            PurchaseRequest.category.label("category"),
            func.count(PurchaseRequest.id).label("count"),
            func.coalesce(func.sum(PurchaseRequest.estimated_cost), 0.0).label("total"),
        )
        .filter(PurchaseRequest.status == "approved"),
        current_user,
    )
    approved_rows = (
        approved_rows
        .group_by(PurchaseRequest.category)
        .all()
    )

    # Query 2: pending (submitted or draft) counts/totals per category
    pending_rows = _scope_to_user(
        db.query(
            PurchaseRequest.category.label("category"),
            func.count(PurchaseRequest.id).label("count"),
            func.coalesce(func.sum(PurchaseRequest.estimated_cost), 0.0).label("total"),
        )
        .filter(PurchaseRequest.status.in_(_PENDING_STATUSES)),
        current_user,
    )
    pending_rows = (
        pending_rows
        .group_by(PurchaseRequest.category)
        .all()
    )

    # Query 3: all distinct categories (any status)
    all_cats = (
        _scope_to_user(
            db.query(PurchaseRequest.category.label("category")),
            current_user,
        )
        .distinct()
        .all()
    )

    approved_map = {row.category: (row.count, row.total) for row in approved_rows}
    pending_map = {row.category: (row.count, row.total) for row in pending_rows}
    categories = sorted({row.category for row in all_cats})

    return [
        CategorySummary(
            category=cat,
            approved_count=approved_map.get(cat, (0, 0.0))[0],
            approved_total=approved_map.get(cat, (0, 0.0))[1],
            pending_count=pending_map.get(cat, (0, 0.0))[0],
            pending_total=pending_map.get(cat, (0, 0.0))[1],
        )
        for cat in categories
    ]
