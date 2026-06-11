from pydantic import BaseModel


class SpendGroup(BaseModel):
    group: str
    count: int
    total_estimated_cost: float


class CategorySummary(BaseModel):
    category: str
    approved_count: int
    approved_total: float
    pending_count: int
    pending_total: float
