from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.deps import _get_request_or_403, get_current_active_user
from app.core.limiter import limiter
from app.db.base import get_db
from app.db.models import AIReview, User
from app.schemas.ai_review import AIReviewResult
from app.services.ai_review_service import generate_ai_review

router = APIRouter(prefix="/requests", tags=["ai-reviews"])


def _review_result(row: AIReview) -> AIReviewResult:
    return AIReviewResult(
        summary=row.summary,
        category=row.category,
        urgency=row.urgency,
        risk_level=row.risk_level,
        missing_info=row.missing_info,
        recommended_action=row.recommended_action,
        rfq_draft=row.rfq_draft,
        confidence=row.confidence,
    )


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


@router.get("/{request_id}/ai-review", response_model=AIReviewResult)
def get_cached_review(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AIReviewResult:
    req = _get_request_or_403(db, request_id, current_user)
    cached = (
        db.query(AIReview)
        .filter_by(request_id=req.id)
        .order_by(AIReview.created_at.desc())
        .first()
    )
    if cached is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI review not found",
        )
    return _review_result(cached)
