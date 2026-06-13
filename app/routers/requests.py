from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import _get_request_or_403, get_current_active_user, require_role
from app.core.limiter import limiter
from app.db.base import get_db
from app.db.models import PurchaseRequest, RequestComment, User
from app.schemas.pagination import PaginatedResponse
from app.schemas.purchase_request import (
    PurchaseRequestCreate,
    PurchaseRequestResponse,
    PurchaseRequestSummary,
    PurchaseRequestUpdate,
)
from app.schemas.request_comment import RequestCommentCreate, RequestCommentResponse
from app.services.approval_engine import route_request
from app.services.audit_service import ACTION_ROUTED, ACTION_SUBMITTED, log_action
from app.services.budget_service import would_exceed_budget
from app.services.notification_service import notify_request_submitted
from app.services.request_sla_service import find_overdue_requests
from app.services.vendor_service import validate_active_vendor_or_400

router = APIRouter(prefix="/requests", tags=["requests"])



@router.post("/", response_model=PurchaseRequestResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
def create_request(
    request: Request,
    body: PurchaseRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("requester")),
):
    validate_active_vendor_or_400(db, body.vendor_id)
    req = PurchaseRequest(
        title=body.title,
        description=body.description,
        category=body.category,
        urgency=body.urgency,
        quantity=body.quantity,
        estimated_cost=body.estimated_cost,
        vendor_id=body.vendor_id,
        vendor_name=body.vendor_name,
        department_id=current_user.department_id,
        justification=body.justification,
        status="draft",
        requester_id=current_user.id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return PurchaseRequestResponse.model_validate(req)


@router.get("/", response_model=PaginatedResponse[PurchaseRequestSummary])
@limiter.limit("30/minute")
def list_requests(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
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
    total = q.count()
    items = [PurchaseRequestSummary.model_validate(r) for r in q.offset(skip).limit(limit).all()]
    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/overdue", response_model=PaginatedResponse[PurchaseRequestSummary])
def list_overdue_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("manager", "finance", "admin")),
):
    q = find_overdue_requests(db, current_user)
    total = q.count()
    items = [PurchaseRequestSummary.model_validate(r) for r in q.offset(skip).limit(limit).all()]
    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)


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
    if "vendor_id" in update_data:
        validate_active_vendor_or_400(db, update_data["vendor_id"])
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
    budget_warning = would_exceed_budget(db, req)
    req.status = "pending_review"
    req.submitted_at = datetime.now(timezone.utc)
    req.approval_due_at = req.submitted_at + timedelta(days=settings.approval_sla_days)
    db.commit()
    log_action(db, req.id, current_user.id, ACTION_SUBMITTED, old_status, "pending_review")
    if budget_warning is not None:
        log_action(db, req.id, current_user.id, "budget_warning", None, None, budget_warning)
    req = route_request(db, req)
    log_action(db, req.id, None, ACTION_ROUTED, "pending_review", req.status)
    approver_emails = [
        u.email
        for u in db.query(User).filter(User.role == "manager", User.is_active == True).all()
    ]
    notify_request_submitted(req.title, approver_emails)
    response = PurchaseRequestResponse.model_validate(req)
    response.budget_warning = budget_warning
    return response


@router.get("/{request_id}/comments", response_model=list[RequestCommentResponse])
def list_comments(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    _get_request_or_403(db, request_id, current_user)
    q = db.query(RequestComment).filter(RequestComment.request_id == request_id)
    if current_user.role == "requester":
        q = q.filter(RequestComment.visibility == "public")
    comments = q.order_by(RequestComment.created_at.asc()).all()
    return [RequestCommentResponse.model_validate(comment) for comment in comments]


@router.post("/{request_id}/comments", response_model=RequestCommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(
    request_id: int,
    body: RequestCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    _get_request_or_403(db, request_id, current_user)
    if body.visibility == "finance_internal" and current_user.role not in ("admin", "finance"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only finance or admin can create internal comments")
    comment = RequestComment(
        request_id=request_id,
        author_id=current_user.id,
        body=body.body,
        visibility=body.visibility,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    log_action(db, request_id, current_user.id, "comment", None, None, body.visibility)
    return RequestCommentResponse.model_validate(comment)
