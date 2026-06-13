from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class VendorCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    contact_name: Optional[str] = Field(default=None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=50)
    category: Optional[str] = Field(default=None, max_length=100)
    payment_terms: Optional[str] = Field(default=None, max_length=100)
    is_preferred: bool = False
    is_active: bool = True
    notes: Optional[str] = None


class VendorUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    contact_name: Optional[str] = Field(default=None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=50)
    category: Optional[str] = Field(default=None, max_length=100)
    payment_terms: Optional[str] = Field(default=None, max_length=100)
    is_preferred: Optional[bool] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class VendorResponse(BaseModel):
    id: int
    name: str
    contact_name: Optional[str]
    email: Optional[EmailStr]
    phone: Optional[str]
    category: Optional[str]
    payment_terms: Optional[str]
    is_preferred: bool
    is_active: bool
    notes: Optional[str]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
