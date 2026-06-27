from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import AuthUser, ChangePasswordRequest, LoginRequest, TokenResponse
from app.services.auth import get_current_user
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    hash_password,
    verify_password,
)


router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = authenticate_user(db, payload.username, payload.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token(
        {
            "sub": user.username,
            "role": user.role,
            "display_name": user.display_name,
        }
    )
    return TokenResponse(
        access_token=token,
        user=AuthUser(
            username=user.username,
            display_name=user.display_name,
            role=user.role,
        ),
    )


@router.get("/me", response_model=AuthUser)
def me(request: Request, db: Session = Depends(get_db)) -> AuthUser:
    user = get_current_user(request, db)
    return AuthUser(username=user.username, display_name=user.display_name, role=user.role)


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    user = get_current_user(request, db)
    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")
    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"status": "ok"}
