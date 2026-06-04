from typing import Literal

from pydantic import BaseModel, Field


class AIReviewResult(BaseModel):
    summary: str
    category: str
    urgency: Literal["low", "medium", "high"]
    risk_level: Literal["low", "medium", "high"]
    missing_info: list[str]
    recommended_action: Literal[
        "request_more_info", "manager_review", "finance_review", "ready_for_rfq"
    ]
    rfq_draft: str
    confidence: float = Field(ge=0.0, le=1.0)
