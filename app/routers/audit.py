from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.db.base import get_db
from app.db.models import AuditLog, User
from app.schemas.audit import AuditLogResponse

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


@router.get("/", response_model=list[AuditLogResponse])
def get_recent_audit(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    entries = (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(100)
        .all()
    )
    return [AuditLogResponse.model_validate(e) for e in entries]
