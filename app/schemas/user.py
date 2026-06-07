from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    full_name: str
    role: Literal["requester", "manager", "finance", "admin"]
    department_id: Optional[int] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    department_id: Optional[int] = None


class UserAdminUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[Literal["requester", "manager", "finance", "admin"]] = None
    department_id: Optional[int] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str
    department_id: Optional[int]
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CurrentUser(BaseModel):
    id: int
    email: str
    role: str
    is_active: bool
    model_config = ConfigDict(from_attributes=True)
