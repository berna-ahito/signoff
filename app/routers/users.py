from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user, require_role
from app.core.limiter import limiter
from app.core.security import get_password_hash
from app.db.base import get_db
from app.db.models import User
from app.schemas.user import UserAdminUpdate, UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_active_user)):
    return UserResponse.model_validate(current_user)


@router.get("/", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    users = db.query(User).order_by(User.id.asc()).all()
    return [UserResponse.model_validate(u) for u in users]


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def create_user(
    request: Request,
    body: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user = User(
        email=body.email,
        hashed_password=get_password_hash(body.password),
        full_name=body.full_name,
        role=body.role,
        department_id=body.department_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
@limiter.limit("20/minute")
def update_user(
    request: Request,
    user_id: int,
    body: UserAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    update_data = body.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)
