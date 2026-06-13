from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RequestCommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)
    visibility: Literal["public", "finance_internal"] = "public"


class RequestCommentResponse(BaseModel):
    id: int
    request_id: int
    author_id: int
    body: str
    visibility: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
