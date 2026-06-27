from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.config import settings
from app.services.auth_service import decode_access_token


def get_current_user(request: Request, db: Session) -> models.User:
    username = _username_from_bearer_token(request)
    if username is None and not settings.is_production:
        username = request.headers.get("X-USER-NAME")
    if not username:
        raise HTTPException(status_code=401, detail="Authentication is required")

    user = db.execute(
        select(models.User).where(models.User.username == username)
    ).scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid or inactive user")
    return user


def _username_from_bearer_token(request: Request) -> str | None:
    authorization = request.headers.get("Authorization")
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    payload = decode_access_token(token)
    if payload is None or not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return str(payload["sub"])


def actor_name(user: models.User) -> str:
    return user.display_name or user.username


def ensure_role(user: models.User, allowed_roles: set[str]) -> None:
    if user.role == "ADMIN":
        return
    if user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Permission denied")
