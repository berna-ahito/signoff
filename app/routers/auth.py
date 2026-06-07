from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.limiter import limiter
from app.core.security import create_access_token, verify_password
from app.db.base import get_db
from app.db.models import User
from app.schemas.auth import LoginRequest, Token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
def login(request: Request, body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email, User.is_active == True).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token({"user_id": user.id, "role": user.role})
    return Token(access_token=token, token_type="bearer")
