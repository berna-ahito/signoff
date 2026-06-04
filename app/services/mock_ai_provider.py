from app.db.models import PurchaseRequest
from app.schemas.ai_review import AIReviewResult


class MockAIProvider:
    _URGENCY_MAP: dict[str, str] = {
        "low": "low",
        "medium": "medium",
        "high": "high",
        "critical": "high",
    }

    def review(self, request: PurchaseRequest) -> AIReviewResult:
        urgency = self._URGENCY_MAP.get(request.urgency, "medium")
        risk_level = self._calc_risk(request.estimated_cost)
        missing = self._detect_missing(request)
        recommended_action = self._recommend(risk_level, missing)
        confidence = round(max(0.1, 1.0 - 0.15 * len(missing)), 2)
        summary = (
            f"Purchase request '{request.title}' for {request.quantity} unit(s) "
            f"at an estimated cost of ${request.estimated_cost:.2f}. "
            f"Category: {request.category}. Risk level assessed as {risk_level}."
        )
        rfq_draft = (
            f"Request for Quotation\n\n"
            f"Item: {request.title}\n"
            f"Description: {request.description}\n"
            f"Quantity: {request.quantity}\n"
            f"Category: {request.category}\n"
            f"Estimated Budget: ${request.estimated_cost:.2f}\n"
            f"Justification: {request.justification}"
        )
        return AIReviewResult(
            summary=summary,
            category=request.category,
            urgency=urgency,
            risk_level=risk_level,
            missing_info=missing,
            recommended_action=recommended_action,
            rfq_draft=rfq_draft,
            confidence=confidence,
        )

    def _calc_risk(self, cost: float) -> str:
        if cost >= 10_000:
            return "high"
        if cost >= 1_000:
            return "medium"
        return "low"

    def _detect_missing(self, request: PurchaseRequest) -> list[str]:
        missing: list[str] = []
        if len(request.description) < 50:
            missing.append("detailed description needed")
        if len(request.justification) < 30:
            missing.append("stronger justification needed")
        if request.vendor_id is None:
            missing.append("vendor not specified")
        return missing

    def _recommend(self, risk_level: str, missing: list[str]) -> str:
        if missing:
            return "request_more_info"
        if risk_level == "high":
            return "finance_review"
        if risk_level == "medium":
            return "manager_review"
        return "ready_for_rfq"
