from datetime import datetime, timezone

from sqlalchemy import extract
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Invoice, PurchaseOrder, PurchaseOrderLineItem

PO_TRANSITIONS = {
    "draft": {"issued", "cancelled"},
    "issued": {"vendor_confirmed", "received", "cancelled"},
    "vendor_confirmed": {"received", "cancelled"},
    "received": {"closed"},
    "closed": set(),
    "cancelled": set(),
}


def make_po_number(db: Session) -> str:
    year = datetime.now(timezone.utc).year
    count = db.query(PurchaseOrder).filter(extract("year", PurchaseOrder.created_at) == year).count()
    return f"PF-{year}-{count + 1:04d}"


def line_total(quantity: int, unit_price: float) -> float:
    return round(float(quantity) * float(unit_price), 2)


def purchase_order_total(po: PurchaseOrder) -> float:
    return round(sum(item.total_price for item in po.line_items), 2)


def validate_po_transition(current_status: str, new_status: str) -> None:
    allowed = PO_TRANSITIONS.get(current_status, set())
    if new_status not in allowed:
        raise ValueError(f"Invalid purchase order transition: {current_status} -> {new_status}")


def apply_po_status(po: PurchaseOrder, new_status: str, notes: str | None = None) -> None:
    validate_po_transition(po.status, new_status)
    po.status = new_status
    if notes is not None:
        po.notes = notes
    if new_status == "issued" and po.issued_at is None:
        po.issued_at = datetime.now(timezone.utc)


def validate_po_can_close(db: Session, po: PurchaseOrder) -> None:
    if po.status != "received":
        raise ValueError("Purchase order must be fully received before closeout")
    invoices = db.query(Invoice).filter(Invoice.purchase_order_id == po.id).all()
    if not invoices:
        raise ValueError("Purchase order requires an invoice before closeout")
    for invoice in invoices:
        if invoice.status == "matched":
            return
        if invoice.status == "approved_for_payment" and invoice.notes and invoice.notes.strip():
            return
    raise ValueError("Purchase order requires a matched or approved invoice before closeout")


def build_line_item(purchase_order_id: int, description: str, quantity: int, unit_price: float) -> PurchaseOrderLineItem:
    return PurchaseOrderLineItem(
        purchase_order_id=purchase_order_id,
        description=description,
        quantity=quantity,
        unit_price=unit_price,
        total_price=line_total(quantity, unit_price),
    )


def verify_invoice(invoice: Invoice, po: PurchaseOrder) -> str:
    delta = abs(float(invoice.invoice_amount) - purchase_order_total(po))
    if delta <= settings.invoice_match_tolerance:
        invoice.status = "matched"
    else:
        invoice.status = "mismatch"
    return invoice.status
