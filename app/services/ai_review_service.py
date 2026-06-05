from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import AIReview, PurchaseRequest
from app.schemas.ai_review import AIReviewResult
from app.services.ai_review_base import AIReviewProvider
from app.services.mock_ai_provider import MockAIProvider


def _load_provider() -> AIReviewProvider:
    if settings.ai_provider == "groq":
        from app.services.groq_provider import GroqProvider
        return GroqProvider()
    return MockAIProvider()


_provider: AIReviewProvider = _load_provider()


def _provider_name() -> str:
    return settings.ai_provider


def generate_ai_review(request: PurchaseRequest, db: Session) -> AIReviewResult:
    name = _provider_name()
    cached = (
        db.query(AIReview)
        .filter_by(request_id=request.id, provider_name=name)
        .first()
    )
    if cached is not None:
        return AIReviewResult(
            summary=cached.summary,
            category=cached.category,
            urgency=cached.urgency,
            risk_level=cached.risk_level,
            missing_info=cached.missing_info,
            recommended_action=cached.recommended_action,
            rfq_draft=cached.rfq_draft,
            confidence=cached.confidence,
        )

    result = _provider.review(request)

    row = AIReview(
        request_id=request.id,
        provider_name=name,
        summary=result.summary,
        category=result.category,
        urgency=result.urgency,
        risk_level=result.risk_level,
        missing_info=result.missing_info,
        recommended_action=result.recommended_action,
        rfq_draft=result.rfq_draft,
        confidence=result.confidence,
    )
    db.add(row)
    db.commit()

    return result
