from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


POStatus = Literal["draft", "issued", "vendor_confirmed", "received", "closed", "cancelled"]
ReceivingStatus = Literal["partially_received", "fully_received", "rejected"]
InvoiceStatus = Literal["uploaded", "matched", "mismatch", "approved_for_payment", "rejected"]


class PurchaseOrderLineItemCreate(BaseModel):
    description: str = Field(min_length=2, max_length=500)
    quantity: int = Field(gt=0)
    unit_price: float = Field(ge=0.0)


class PurchaseOrderLineItemResponse(BaseModel):
    id: int
    description: str
    quantity: int
    unit_price: float
    total_price: float
    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderCreate(BaseModel):
    vendor_id: Optional[int] = None
    notes: Optional[str] = None
    line_items: list[PurchaseOrderLineItemCreate] = Field(min_length=1)


class PurchaseOrderStatusUpdate(BaseModel):
    status: POStatus
    notes: Optional[str] = None


class PurchaseOrderResponse(BaseModel):
    id: int
    po_number: str
    request_id: int
    vendor_id: Optional[int]
    status: str
    issued_at: Optional[datetime]
    created_by: int
    notes: Optional[str]
    created_at: datetime
    line_items: list[PurchaseOrderLineItemResponse] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class ReceivingRecordCreate(BaseModel):
    status: ReceivingStatus
    note: Optional[str] = None


class ReceivingRecordResponse(BaseModel):
    id: int
    purchase_order_id: int
    received_by: int
    received_at: datetime
    status: str
    note: Optional[str]
    model_config = ConfigDict(from_attributes=True)


class InvoiceCreate(BaseModel):
    invoice_number: str = Field(min_length=1, max_length=100)
    invoice_amount: float = Field(gt=0.0)
    invoice_date: date
    attachment_id: Optional[int] = None
    notes: Optional[str] = None


class InvoicePaymentApproval(BaseModel):
    note: str = Field(min_length=1, max_length=1000)


class InvoiceResponse(BaseModel):
    id: int
    purchase_order_id: int
    invoice_number: str
    invoice_amount: float
    invoice_date: datetime
    status: str
    attachment_id: Optional[int]
    uploaded_by: int
    notes: Optional[str]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
