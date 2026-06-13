import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import AIReview, PurchaseRequest
from app.schemas.ai_review import AIReviewResult
from app.services.ai_review_base import AIReviewProvider
from app.services.mock_ai_provider import MockAIProvider

logger = logging.getLogger(__name__)

_VALID_RISK_LEVELS = {"low", "medium", "high", "unknown"}
_VALID_ACTIONS = {"approve", "reject", "request_info", "escalate", "review"}


def _sanitize_ai_result(result: dict) -> dict:
    sanitized = dict(result)
    if sanitized.get("risk_level") not in _VALID_RISK_LEVELS:
        logger.warning(
            "AI returned invalid risk_level=%r, defaulting to 'unknown'",
            sanitized.get("risk_level"),
        )
        sanitized["risk_level"] = "unknown"
    if sanitized.get("recommended_action") not in _VALID_ACTIONS:
        logger.warning(
            "AI returned invalid recommended_action=%r, defaulting to 'review'",
            sanitized.get("recommended_action"),
        )
        sanitized["recommended_action"] = "review"
    return sanitized


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

    raw = _provider.review(request)
    safe = _sanitize_ai_result(raw.model_dump())
    result = AIReviewResult(**safe)

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

    if result.risk_level == "high":
        logger.warning(
            "High-risk request #%s: %s - action=%s",
            request.id,
            request.title,
            result.recommended_action,
        )

    return result
