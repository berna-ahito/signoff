import json
import logging

import groq
from pydantic import ValidationError

from app.core.config import settings
from app.db.models import PurchaseRequest
from app.schemas.ai_review import AIReviewResult
from app.services.ai_review_base import AIReviewProvider
from app.services.mock_ai_provider import MockAIProvider

logger = logging.getLogger(__name__)

_PROMPT_TEMPLATE = """You are a procurement analyst. Review the following purchase request and return a JSON object.

Purchase Request:
- Title: {title}
- Description: {description}
- Category: {category}
- Urgency: {urgency}
- Estimated Cost: ${estimated_cost:.2f}
- Quantity: {quantity}
- Justification: {justification}

Return ONLY a valid JSON object with these exact fields:
- "summary": string — a 1-2 sentence summary of the request
- "category": string — the procurement category
- "urgency": one of exactly: "low", "medium", "high"
- "risk_level": one of exactly: "low", "medium", "high"
- "missing_info": array of strings — list missing or unclear information, or empty array []
- "recommended_action": one of exactly: "request_more_info", "manager_review", "finance_review", "ready_for_rfq"
- "rfq_draft": string — a short RFQ draft paragraph
- "confidence": float between 0.0 and 1.0

Respond with JSON only. No explanation text."""


class GroqProvider(AIReviewProvider):
    def review(self, request: PurchaseRequest) -> AIReviewResult:
        # Prevent prompt injection via user-controlled fields
        safe_title = request.title.replace("\n", " ").replace("\r", " ")[:200]
        safe_description = request.description.replace("\n", " ").replace("\r", " ")[:500]
        safe_justification = request.justification.replace("\n", " ").replace("\r", " ")[:300]
        prompt = _PROMPT_TEMPLATE.format(
            title=safe_title,
            description=safe_description,
            category=request.category,
            urgency=request.urgency,
            estimated_cost=request.estimated_cost,
            quantity=request.quantity,
            justification=safe_justification,
        )
        try:
            client = groq.Groq(api_key=settings.groq_api_key)
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            data = json.loads(response.choices[0].message.content)
            return AIReviewResult.model_validate(data)
        except (ValidationError, groq.APIError, Exception) as exc:
            logger.warning("Groq provider failed (%s), falling back to MockProvider", exc)
            return MockAIProvider().review(request)
