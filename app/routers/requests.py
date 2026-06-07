from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.deps import _get_request_or_403, get_current_active_user, require_role
from app.core.limiter import limiter
from app.db.base import get_db
from app.db.models import PurchaseRequest, User
from app.schemas.purchase_request import (
    PurchaseRequestCreate,
    PurchaseRequestResponse,
    PurchaseRequestSummary,
    PurchaseRequestUpdate,
)
from app.services.approval_engine import route_request
from app.services.audit_service import ACTION_ROUTED, ACTION_SUBMITTED, log_action

router = APIRouter(prefix="/requests", tags=["requests"])



@router.post("/", response_model=PurchaseRequestResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
def create_request(
    request: Request,
    body: PurchaseRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("requester")),
):
    req = PurchaseRequest(
        title=body.title,
        description=body.description,
        category=body.category,
        urgency=body.urgency,
        quantity=body.quantity,
        estimated_cost=body.estimated_cost,
        vendor_id=body.vendor_id,
        justification=body.justification,
        status="draft",
        requester_id=current_user.id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return PurchaseRequestResponse.model_validate(req)


@router.get("/", response_model=list[PurchaseRequestSummary])
def list_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    q = db.query(PurchaseRequest)
    if current_user.role == "requester":
        q = q.filter(PurchaseRequest.requester_id == current_user.id)
    elif current_user.role == "manager":
        q = q.filter(
            (PurchaseRequest.assigned_role == "manager") |
            (PurchaseRequest.requester_id == current_user.id)
        )
    elif current_user.role == "finance":
        q = q.filter(
            (PurchaseRequest.assigned_role == "finance") |
            (PurchaseRequest.requester_id == current_user.id)
        )
    return [PurchaseRequestSummary.model_validate(r) for r in q.all()]


@router.get("/{request_id}", response_model=PurchaseRequestResponse)
def get_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    req = _get_request_or_403(db, request_id, current_user)
    return PurchaseRequestResponse.model_validate(req)


@router.patch("/{request_id}", response_model=PurchaseRequestResponse)
def update_request(
    request_id: int,
    body: PurchaseRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("requester")),
):
    req = _get_request_or_403(db, request_id, current_user)
    if req.status != "draft":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Can only edit draft requests")
    update_data = body.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(req, field, value)
    db.commit()
    db.refresh(req)
    return PurchaseRequestResponse.model_validate(req)


@router.post("/{request_id}/submit", response_model=PurchaseRequestResponse)
@limiter.limit("20/minute")
def submit_request(
    request: Request,
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("requester")),
):
    req = _get_request_or_403(db, request_id, current_user)
    if req.status != "draft":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request is not in draft status")
    old_status = req.status
    req.status = "pending_review"
    db.commit()
    log_action(db, req.id, current_user.id, ACTION_SUBMITTED, old_status, "pending_review")
    req = route_request(db, req)
    log_action(db, req.id, None, ACTION_ROUTED, "pending_review", req.status)
    return PurchaseRequestResponse.model_validate(req)
