from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.models.base import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    ResetPasswordResponse,
    TokenResponse,
    UserOut,
)
from app.services.auth_service import login_user, register_user, reset_password

router = APIRouter()


@router.post("/register", response_model=TokenResponse)
def register(body: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return register_user(db, body)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return login_user(db, body)


@router.post("/reset-password", response_model=ResetPasswordResponse)
def reset_password_route(
    body: ResetPasswordRequest, db: Session = Depends(get_db)
) -> ResetPasswordResponse:
    return reset_password(db, body)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        is_admin=user.is_admin,
        created_at=user.created_at,
    )


@router.post("/logout")
def logout(user: User = Depends(get_current_user)) -> dict[str, bool]:
    # JWT is stateless — client discards the token.
    _ = user
    return {"ok": True}
