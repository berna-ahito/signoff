from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user, require_role
from app.core.limiter import limiter
from app.db.base import get_db
from app.db.models import User, Vendor
from app.schemas.vendor import VendorCreate, VendorResponse, VendorUpdate

router = APIRouter(prefix="/vendors", tags=["vendors"])


def _vendor_response(vendor: Vendor) -> VendorResponse:
    if vendor.email is None and vendor.contact_email is not None:
        vendor.email = vendor.contact_email
    return VendorResponse.model_validate(vendor)


@router.get("/", response_model=list[VendorResponse])
def list_vendors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    vendors = db.query(Vendor).filter(Vendor.is_active == True).order_by(Vendor.name.asc()).all()
    return [_vendor_response(v) for v in vendors]


@router.post("/", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def create_vendor(
    request: Request,
    body: VendorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "finance")),
):
    vendor = Vendor(**body.model_dump())
    vendor.contact_email = str(body.email) if body.email is not None else None
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return _vendor_response(vendor)


@router.get("/{vendor_id}", response_model=VendorResponse)
def get_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    vendor = db.get(Vendor, vendor_id)
    if vendor is None or not vendor.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    return _vendor_response(vendor)


@router.patch("/{vendor_id}", response_model=VendorResponse)
@limiter.limit("20/minute")
def update_vendor(
    request: Request,
    vendor_id: int,
    body: VendorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "finance")),
):
    vendor = db.get(Vendor, vendor_id)
    if vendor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(vendor, field, value)
        if field == "email":
            vendor.contact_email = str(value) if value is not None else None
    db.commit()
    db.refresh(vendor)
    return _vendor_response(vendor)
