from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import PyJWTError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.base import get_db
from app.db.models import PurchaseRequest, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except PyJWTError:
        raise credentials_exception
    user = db.get(User, user_id)
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user


def require_role(*allowed_roles: str):
    def _require_role(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user
    return _require_role


def _get_request_or_403(db: Session, request_id: int, current_user: User) -> PurchaseRequest:
    req = db.get(PurchaseRequest, request_id)
    if req is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    if current_user.role == "admin":
        return req
    if current_user.role == "requester" and req.requester_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if current_user.role == "manager" and req.assigned_role != "manager" and req.requester_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if current_user.role == "finance" and req.assigned_role != "finance" and req.requester_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return req
