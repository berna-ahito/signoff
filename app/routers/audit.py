from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.db.base import get_db
from app.db.models import AuditLog, User
from app.schemas.audit import AuditLogResponse
from app.schemas.pagination import PaginatedResponse

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/requests/{request_id}", response_model=list[AuditLogResponse])
def get_request_audit(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    entries = (
        db.query(AuditLog)
        .filter(AuditLog.request_id == request_id)
        .order_by(AuditLog.created_at.asc())
        .all()
    )
    return [AuditLogResponse.model_validate(e) for e in entries]


@router.get("/", response_model=PaginatedResponse[AuditLogResponse])
def get_recent_audit(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    q = db.query(AuditLog).order_by(AuditLog.created_at.desc())
    total = q.count()
    items = [AuditLogResponse.model_validate(e) for e in q.offset(skip).limit(limit).all()]
    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)
