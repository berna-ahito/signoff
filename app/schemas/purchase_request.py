from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.ai_review import AIReviewResult

VALID_URGENCY = Literal["low", "medium", "high", "critical"]
VALID_STATUS = Literal["draft", "pending_review", "pending_approval", "needs_rule", "approved", "rejected", "needs_more_info"]


class PurchaseRequestCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=2000)
    category: str = Field(min_length=2, max_length=100)
    urgency: VALID_URGENCY
    quantity: int = Field(gt=0)
    estimated_cost: float = Field(gt=0.0)
    vendor_id: Optional[int] = None
    justification: str = Field(min_length=10, max_length=1000)


class PurchaseRequestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    urgency: Optional[VALID_URGENCY] = None
    quantity: Optional[int] = Field(default=None, gt=0)
    estimated_cost: Optional[float] = Field(default=None, gt=0.0)
    vendor_id: Optional[int] = None
    justification: Optional[str] = None


class PurchaseRequestResponse(BaseModel):
    id: int
    title: str
    description: str
    category: str
    urgency: str
    quantity: int
    estimated_cost: float
    vendor_id: Optional[int]
    justification: str
    status: str
    requester_id: int
    assigned_role: Optional[str]
    created_at: datetime
    updated_at: datetime
    ai_review: Optional[AIReviewResult] = None
    model_config = ConfigDict(from_attributes=True)


class PurchaseRequestSummary(BaseModel):
    id: int
    title: str
    category: str
    urgency: str
    status: str
    estimated_cost: float
    requester_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
