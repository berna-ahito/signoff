import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.limiter import limiter
from app.core.security import create_access_token, verify_password
from app.db.base import get_db
from app.db.models import RefreshToken, User
from app.schemas.auth import AccessToken, LoginRequest, LogoutRequest, RefreshRequest, Token

router = APIRouter(prefix="/auth", tags=["auth"])


def _sha256_hex(value: str) -> str:
    """SHA-256 hex digest of a string — keeps payload under bcrypt's 72-byte limit."""
    return hashlib.sha256(value.encode()).hexdigest()


def _create_refresh_token(db: Session, user_id: int) -> str:
    raw_token = secrets.token_urlsafe(64)
    token_prefix = raw_token[:16]
    # SHA-256 first so the input to bcrypt is always exactly 64 hex chars (< 72 bytes).
    intermediate = _sha256_hex(raw_token)
    token_hash = bcrypt.hashpw(intermediate.encode(), bcrypt.gensalt()).decode()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    db_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        token_prefix=token_prefix,
        expires_at=expires_at,
    )
    db.add(db_token)
    db.commit()
    return raw_token


def _find_valid_refresh_token(db: Session, token: str) -> RefreshToken:
    """Look up a non-revoked, non-expired RefreshToken matching token.

    Filters by token_prefix index first (O(1) lookup), then bcrypt-checks
    the single matching row. Raises HTTP 401 if not found or invalid.
    """
    now = datetime.now(timezone.utc)
    token_prefix = token[:16]
    candidate = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token_prefix == token_prefix,
            RefreshToken.revoked == False,  # noqa: E712
            RefreshToken.expires_at > now,
        )
        .first()
    )
    intermediate = _sha256_hex(token)
    if candidate and bcrypt.checkpw(intermediate.encode(), candidate.token_hash.encode()):
        return candidate
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
def login(request: Request, body: LoginRequest, db: Session = Depends(get_db)) -> Token:
    user = db.query(User).filter(User.email == body.email, User.is_active == True).first()  # noqa: E712
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token({"user_id": user.id, "role": user.role})
    refresh_token = _create_refresh_token(db, user.id)
    return Token(access_token=access_token, token_type="bearer", refresh_token=refresh_token)


@router.post("/refresh", response_model=AccessToken)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)) -> AccessToken:
    db_token = _find_valid_refresh_token(db, body.refresh_token)
    user = db.query(User).filter(User.id == db_token.user_id, User.is_active == True).first()  # noqa: E712
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token({"user_id": user.id, "role": user.role})
    return AccessToken(access_token=access_token, token_type="bearer")


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(body: LogoutRequest, db: Session = Depends(get_db)) -> Response:
    db_token = _find_valid_refresh_token(db, body.refresh_token)
    db_token.revoked = True
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
