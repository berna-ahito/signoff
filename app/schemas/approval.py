from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ApprovalRuleCreate(BaseModel):
    name: str
    min_amount: float = Field(ge=0.0)
    max_amount: Optional[float] = None
    category: Optional[str] = None
    required_role: Literal["manager", "finance", "admin"]
    priority: int = Field(ge=1)


class ApprovalRuleResponse(BaseModel):
    id: int
    name: str
    min_amount: float
    max_amount: Optional[float]
    category: Optional[str]
    required_role: str
    priority: int
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class ApprovalDecisionCreate(BaseModel):
    decision: Literal["approved", "rejected", "needs_more_info"]
    note: Optional[str] = None


class ApprovalDecisionResponse(BaseModel):
    id: int
    request_id: int
    actor_id: int
    decision: str
    note: Optional[str]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
