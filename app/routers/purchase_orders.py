from datetime import datetime
from html import escape

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.deps import (
    _get_invoice_or_403,
    _get_procurement_request_or_403,
    _get_purchase_order_or_403,
    _get_request_or_403,
    get_current_active_user,
    require_role,
)
from app.core.limiter import limiter
from app.db.base import get_db
from app.db.models import Invoice, PurchaseOrder, ReceivingRecord, RequestAttachment, User
from app.schemas.pagination import PaginatedResponse
from app.schemas.purchase_order import (
    InvoiceCreate,
    InvoicePaymentApproval,
    InvoiceResponse,
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    PurchaseOrderStatusUpdate,
    ReceivingRecordCreate,
    ReceivingRecordResponse,
)
from app.services.audit_service import ACTION_STATUS_CHANGE, log_action
from app.services.purchase_order_service import (
    apply_po_status,
    build_line_item,
    make_po_number,
    purchase_order_total,
    validate_po_can_close,
    verify_invoice,
)
from app.services.vendor_service import validate_active_vendor_or_400

router = APIRouter(tags=["purchase-orders"])


@router.post("/requests/{request_id}/purchase-order", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def create_purchase_order(
    request: Request,
    request_id: int,
    body: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "finance")),
):
    req = _get_procurement_request_or_403(db, request_id, current_user)
    if req.status != "approved":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request must be approved before creating a purchase order")
    if db.query(PurchaseOrder).filter(PurchaseOrder.request_id == request_id).first() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Purchase order already exists for request")

    vendor_id = body.vendor_id if body.vendor_id is not None else req.vendor_id
    validate_active_vendor_or_400(db, vendor_id)
    po = PurchaseOrder(
        po_number=make_po_number(db),
        request_id=request_id,
        vendor_id=vendor_id,
        status="draft",
        created_by=current_user.id,
        notes=body.notes,
    )
    db.add(po)
    db.commit()
    db.refresh(po)

    for item in body.line_items:
        db.add(build_line_item(po.id, item.description, item.quantity, item.unit_price))
    db.commit()
    db.refresh(po)
    log_action(db, request_id, current_user.id, "purchase_order_created", None, po.status, po.po_number)
    return PurchaseOrderResponse.model_validate(po)


@router.get("/purchase-orders/", response_model=PaginatedResponse[PurchaseOrderResponse])
def list_purchase_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "finance")),
):
    q = db.query(PurchaseOrder).order_by(PurchaseOrder.created_at.desc())
    total = q.count()
    items = [PurchaseOrderResponse.model_validate(po) for po in q.offset(skip).limit(limit).all()]
    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/purchase-orders/{purchase_order_id}", response_model=PurchaseOrderResponse)
def get_purchase_order(
    purchase_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    po = _get_purchase_order_or_403(db, purchase_order_id, current_user)
    return PurchaseOrderResponse.model_validate(po)


@router.patch("/purchase-orders/{purchase_order_id}/status", response_model=PurchaseOrderResponse)
@limiter.limit("20/minute")
def update_purchase_order_status(
    request: Request,
    purchase_order_id: int,
    body: PurchaseOrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "finance")),
):
    po = _get_purchase_order_or_403(db, purchase_order_id, current_user)
    old_status = po.status
    try:
        if body.status == "closed":
            validate_po_can_close(db, po)
        apply_po_status(po, body.status, body.notes)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    db.commit()
    db.refresh(po)
    log_action(db, po.request_id, current_user.id, ACTION_STATUS_CHANGE, old_status, po.status, body.notes)
    return PurchaseOrderResponse.model_validate(po)


@router.get("/purchase-orders/{purchase_order_id}/pdf", response_class=HTMLResponse)
def get_purchase_order_pdf(
    purchase_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "finance")),
):
    po = _get_purchase_order_or_403(db, purchase_order_id, current_user)
    rows = "".join(
        f"<tr><td>{escape(item.description)}</td><td>{item.quantity}</td><td>{item.unit_price:.2f}</td><td>{item.total_price:.2f}</td></tr>"
        for item in po.line_items
    )
    safe_po_number = escape(po.po_number)
    html = f"""
    <html>
      <head><title>{safe_po_number}</title></head>
      <body>
        <h1>Purchase Order {safe_po_number}</h1>
        <p>Status: {escape(po.status)}</p>
        <p>Request: {po.request_id}</p>
        <table>
          <thead><tr><th>Description</th><th>Quantity</th><th>Unit Price</th><th>Total</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
        <p>Total: {purchase_order_total(po):.2f}</p>
      </body>
    </html>
    """
    return HTMLResponse(content=html)


@router.post("/purchase-orders/{purchase_order_id}/receiving", response_model=ReceivingRecordResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
def create_receiving_record(
    request: Request,
    purchase_order_id: int,
    body: ReceivingRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    po = _get_purchase_order_or_403(db, purchase_order_id, current_user)
    req = _get_request_or_403(db, po.request_id, current_user)
    if current_user.role not in ("admin", "finance") and req.requester_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if po.status not in ("issued", "vendor_confirmed"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Purchase order is not in a receivable state")
    record = ReceivingRecord(
        purchase_order_id=po.id,
        received_by=current_user.id,
        status=body.status,
        note=body.note,
    )
    db.add(record)
    old_status = po.status
    if body.status == "fully_received" and po.status in ("issued", "vendor_confirmed"):
        po.status = "received"
    db.commit()
    db.refresh(record)
    db.refresh(po)
    log_action(db, po.request_id, current_user.id, "receiving", old_status, po.status, body.note)
    return ReceivingRecordResponse.model_validate(record)


@router.post("/purchase-orders/{purchase_order_id}/invoices", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def create_invoice(
    request: Request,
    purchase_order_id: int,
    body: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "finance")),
):
    po = _get_purchase_order_or_403(db, purchase_order_id, current_user)
    if body.attachment_id is not None:
        attachment = db.get(RequestAttachment, body.attachment_id)
        if attachment is None or attachment.request_id != po.request_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    invoice = Invoice(
        purchase_order_id=po.id,
        invoice_number=body.invoice_number,
        invoice_amount=body.invoice_amount,
        invoice_date=datetime.combine(body.invoice_date, datetime.min.time()),
        attachment_id=body.attachment_id,
        uploaded_by=current_user.id,
        notes=body.notes,
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    log_action(db, po.request_id, current_user.id, "invoice_uploaded", None, invoice.status, invoice.invoice_number)
    return InvoiceResponse.model_validate(invoice)


@router.get("/purchase-orders/{purchase_order_id}/invoices", response_model=list[InvoiceResponse])
def list_invoices(
    purchase_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "finance")),
):
    po = _get_purchase_order_or_403(db, purchase_order_id, current_user)
    invoices = db.query(Invoice).filter(Invoice.purchase_order_id == po.id).order_by(Invoice.created_at.asc()).all()
    return [InvoiceResponse.model_validate(invoice) for invoice in invoices]


@router.post("/invoices/{invoice_id}/verify", response_model=InvoiceResponse)
@limiter.limit("20/minute")
def verify_invoice_endpoint(
    request: Request,
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "finance")),
):
    invoice = _get_invoice_or_403(db, invoice_id, current_user)
    po = db.get(PurchaseOrder, invoice.purchase_order_id)
    old_status = invoice.status
    new_status = verify_invoice(invoice, po)
    db.commit()
    db.refresh(invoice)
    log_action(db, po.request_id, current_user.id, "invoice_verified", old_status, new_status, invoice.notes)
    return InvoiceResponse.model_validate(invoice)


@router.post("/invoices/{invoice_id}/approve-payment", response_model=InvoiceResponse)
@limiter.limit("20/minute")
def approve_invoice_for_payment(
    request: Request,
    invoice_id: int,
    body: InvoicePaymentApproval,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "finance")),
):
    note = body.note.strip()
    if not note:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Finance note is required")
    invoice = _get_invoice_or_403(db, invoice_id, current_user)
    if invoice.status not in ("matched", "mismatch"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invoice must be matched or mismatch before payment approval")
    po = db.get(PurchaseOrder, invoice.purchase_order_id)
    old_status = invoice.status
    invoice.status = "approved_for_payment"
    invoice.notes = note
    db.commit()
    db.refresh(invoice)
    log_action(db, po.request_id, current_user.id, "invoice_approved_for_payment", old_status, invoice.status, note)
    return InvoiceResponse.model_validate(invoice)
