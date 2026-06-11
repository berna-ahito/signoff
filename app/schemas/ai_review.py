from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AIReviewResult(BaseModel):
    summary: str
    category: str
    urgency: Literal["low", "medium", "high"]
    risk_level: Literal["low", "medium", "high", "unknown"]
    missing_info: list[str]
    recommended_action: Literal["approve", "reject", "request_info", "escalate", "review"]
    rfq_draft: str
    confidence: float = Field(ge=0.0, le=1.0)
    model_config = ConfigDict(from_attributes=True)
