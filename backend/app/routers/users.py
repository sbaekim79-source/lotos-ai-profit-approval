from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import UserCreate, UserRead
from app.services.auth import ensure_role, get_current_user
from app.services.auth_service import hash_password


router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)) -> list[UserRead]:
    users = db.execute(select(models.User).order_by(models.User.username)).scalars()
    return [_to_user_read(user) for user in users]


@router.post("", response_model=UserRead)
def create_user(
    payload: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> UserRead:
    ensure_role(get_current_user(request, db), {"ADMIN"})
    existing = db.execute(
        select(models.User).where(models.User.username == payload.username)
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=400, detail="Username already exists")

    user_data = payload.model_dump(exclude={"password"})
    if payload.password:
        user_data["hashed_password"] = hash_password(payload.password)
    user = models.User(**user_data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return _to_user_read(user)


@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    payload: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> UserRead:
    ensure_role(get_current_user(request, db), {"ADMIN"})
    user = db.get(models.User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    duplicate = db.execute(
        select(models.User).where(
            models.User.username == payload.username,
            models.User.id != user_id,
        )
    ).scalar_one_or_none()
    if duplicate is not None:
        raise HTTPException(status_code=400, detail="Username already exists")

    for key, value in payload.model_dump(exclude={"password"}).items():
        setattr(user, key, value)
    if payload.password:
        user.hashed_password = hash_password(payload.password)
    db.commit()
    db.refresh(user)
    return _to_user_read(user)


@router.delete("/{user_id}", response_model=UserRead)
def deactivate_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
) -> UserRead:
    ensure_role(get_current_user(request, db), {"ADMIN"})
    user = db.get(models.User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    db.commit()
    db.refresh(user)
    return _to_user_read(user)


def _to_user_read(user: models.User) -> UserRead:
    return UserRead(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        email=user.email,
        role=user.role,
        department=user.department,
        is_active=user.is_active,
    )
