from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, LargeBinary, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base


def _now():
    return datetime.now(timezone.utc)


class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(20), unique=True, nullable=True)
    monthly_budget = Column(Float, nullable=False, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_now)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_now)


class Vendor(Base):
    __tablename__ = "vendors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=True)
    contact_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    category = Column(String(100), nullable=True)
    payment_terms = Column(String(100), nullable=True)
    is_preferred = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_now)


class PurchaseRequest(Base):
    __tablename__ = "purchase_requests"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    urgency = Column(String(50), nullable=False)
    quantity = Column(Integer, nullable=False)
    estimated_cost = Column(Float, nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=True)
    vendor_name = Column(String(255), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    justification = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="draft")
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_role = Column(String(50), nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    approval_due_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    ai_review = relationship("AIReview", back_populates="request", uselist=False)

    @property
    def overdue(self) -> bool:
        if self.status != "pending_approval" or self.approval_due_at is None:
            return False
        due_at = self.approval_due_at
        if due_at.tzinfo is None:
            due_at = due_at.replace(tzinfo=timezone.utc)
        return due_at < _now()


class ApprovalRule(Base):
    __tablename__ = "approval_rules"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    min_amount = Column(Float, nullable=False)
    max_amount = Column(Float, nullable=True)
    category = Column(String(100), nullable=True)
    required_role = Column(String(50), nullable=False)
    priority = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_now)


class ApprovalDecision(Base):
    __tablename__ = "approval_decisions"
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("purchase_requests.id"), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    decision = Column(String(50), nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_now)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("purchase_requests.id"), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    old_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_now)


class AIReview(Base):
    __tablename__ = "ai_reviews"
    __table_args__ = (UniqueConstraint("request_id", "provider_name"),)

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("purchase_requests.id"), nullable=False)
    provider_name = Column(String(50), nullable=False)
    summary = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    urgency = Column(String(50), nullable=False)
    risk_level = Column(String(50), nullable=False)
    missing_info = Column(JSON, nullable=False)
    recommended_action = Column(String(100), nullable=False)
    rfq_draft = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    created_at = Column(DateTime, default=_now)

    request = relationship("PurchaseRequest", back_populates="ai_review")


class RequestAttachment(Base):
    __tablename__ = "request_attachments"
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("purchase_requests.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    file_data = Column(LargeBinary, nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=_now)


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String(20), unique=True, nullable=False, index=True)
    request_id = Column(Integer, ForeignKey("purchase_requests.id"), unique=True, nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=True)
    status = Column(String(50), nullable=False, default="draft")
    issued_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_now)

    request = relationship("PurchaseRequest")
    line_items = relationship("PurchaseOrderLineItem", back_populates="purchase_order", cascade="all, delete-orphan")


class PurchaseOrderLineItem(Base):
    __tablename__ = "purchase_order_line_items"
    id = Column(Integer, primary_key=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    description = Column(String(500), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)

    purchase_order = relationship("PurchaseOrder", back_populates="line_items")


class ReceivingRecord(Base):
    __tablename__ = "receiving_records"
    id = Column(Integer, primary_key=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    received_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    received_at = Column(DateTime, default=_now)
    status = Column(String(50), nullable=False)
    note = Column(Text, nullable=True)


class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    invoice_number = Column(String(100), nullable=False)
    invoice_amount = Column(Float, nullable=False)
    invoice_date = Column(DateTime, nullable=False)
    status = Column(String(50), nullable=False, default="uploaded")
    attachment_id = Column(Integer, ForeignKey("request_attachments.id"), nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_now)


class RequestComment(Base):
    __tablename__ = "request_comments"
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("purchase_requests.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    body = Column(Text, nullable=False)
    visibility = Column(String(50), nullable=False, default="public")
    created_at = Column(DateTime, default=_now)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(255), nullable=False, unique=True)
    token_prefix = Column(String(16), index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=_now)
