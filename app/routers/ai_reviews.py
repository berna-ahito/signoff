from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.deps import _get_request_or_403, get_current_active_user
from app.core.limiter import limiter
from app.db.base import get_db
from app.db.models import User
from app.schemas.ai_review import AIReviewResult
from app.services.ai_review_service import generate_ai_review

router = APIRouter(prefix="/requests", tags=["ai-reviews"])


@router.post("/{request_id}/ai-review", response_model=AIReviewResult)
@limiter.limit("10/minute")
def generate_review(
    request_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AIReviewResult:
    req = _get_request_or_403(db, request_id, current_user)
    return generate_ai_review(req, db)
