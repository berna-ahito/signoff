from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user
from app.db.base import get_db
from app.db.models import PurchaseRequest, User
from app.schemas.ai_review import AIReviewResult
from app.services.ai_review_service import generate_ai_review

router = APIRouter(prefix="/requests", tags=["ai-reviews"])


def _get_request_or_403(db: Session, request_id: int, current_user: User) -> PurchaseRequest:
    req = db.get(PurchaseRequest, request_id)
    if req is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    if current_user.role == "admin":
        return req
    if current_user.role == "requester" and req.requester_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if current_user.role == "manager" and req.assigned_role != "manager" and req.requester_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if current_user.role == "finance" and req.assigned_role != "finance" and req.requester_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return req


@router.post("/{request_id}/ai-review", response_model=AIReviewResult)
def generate_review(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AIReviewResult:
    req = _get_request_or_403(db, request_id, current_user)
    return generate_ai_review(req)
