from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import Vendor


def validate_active_vendor_or_400(db: Session, vendor_id: int | None) -> Vendor | None:
    if vendor_id is None:
        return None
    vendor = db.get(Vendor, vendor_id)
    if vendor is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vendor not found")
    if not vendor.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vendor is inactive")
    return vendor
