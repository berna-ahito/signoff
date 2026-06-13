from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    code: str = Field(min_length=2, max_length=20)
    monthly_budget: float = Field(ge=0.0)
    is_active: bool = True


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    code: Optional[str] = Field(default=None, min_length=2, max_length=20)
    monthly_budget: Optional[float] = Field(default=None, ge=0.0)
    is_active: Optional[bool] = None


class DepartmentResponse(BaseModel):
    id: int
    name: str
    code: Optional[str]
    monthly_budget: float
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DepartmentBudgetSummary(BaseModel):
    department_id: int
    monthly_budget: float
    approved_spend_this_month: float
    pending_spend_this_month: float
    remaining_budget: float
    over_budget: bool
