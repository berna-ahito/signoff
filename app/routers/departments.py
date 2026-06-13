from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.core.limiter import limiter
from app.db.base import get_db
from app.db.models import Department, User
from app.schemas.department import DepartmentBudgetSummary, DepartmentCreate, DepartmentResponse, DepartmentUpdate
from app.services.budget_service import budget_summary

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("/", response_model=list[DepartmentResponse])
def list_departments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "finance")),
):
    departments = db.query(Department).order_by(Department.name.asc()).all()
    return [DepartmentResponse.model_validate(d) for d in departments]


@router.post("/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def create_department(
    request: Request,
    body: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    existing = db.query(Department).filter((Department.name == body.name) | (Department.code == body.code)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department already exists")
    department = Department(
        name=body.name,
        code=body.code,
        monthly_budget=body.monthly_budget,
        is_active=body.is_active,
    )
    db.add(department)
    db.commit()
    db.refresh(department)
    return DepartmentResponse.model_validate(department)


@router.patch("/{department_id}", response_model=DepartmentResponse)
@limiter.limit("20/minute")
def update_department(
    request: Request,
    department_id: int,
    body: DepartmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    department = db.get(Department, department_id)
    if department is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(department, field, value)
    db.commit()
    db.refresh(department)
    return DepartmentResponse.model_validate(department)


@router.get("/{department_id}/budget-summary", response_model=DepartmentBudgetSummary)
def get_budget_summary(
    department_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "finance")),
):
    department = db.get(Department, department_id)
    if department is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    return DepartmentBudgetSummary(**budget_summary(db, department))
