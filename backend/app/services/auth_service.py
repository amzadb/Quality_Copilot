"""User registration, login, and admin seeding."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.config import settings
from app.core.errors import AppError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User, UserSettings
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    ResetPasswordResponse,
    TokenResponse,
    UserOut,
)


def _to_user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        is_admin=user.is_admin,
        created_at=user.created_at,
    )


def _ensure_settings(db: Session, user: User) -> UserSettings:
    if user.settings is not None:
        return user.settings
    row = UserSettings(
        user_id=user.id,
        jira={},
        git_provider={},
        testrail={},
        llm={},
    )
    db.add(row)
    db.flush()
    return row


def register_user(db: Session, body: RegisterRequest) -> TokenResponse:
    username = body.username.strip()
    if db.query(User).filter_by(username=username).first():
        raise AppError(
            status_code=409,
            code="USERNAME_TAKEN",
            message=f"Username '{username}' is already taken.",
        )
    email = (body.email or "").strip() or None
    if email and db.query(User).filter_by(email=email).first():
        raise AppError(
            status_code=409,
            code="EMAIL_TAKEN",
            message=f"Email '{email}' is already registered.",
        )

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(body.password),
        is_admin=False,
    )
    db.add(user)
    db.flush()
    _ensure_settings(db, user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.username)
    return TokenResponse(access_token=token, user=_to_user_out(user))


def login_user(db: Session, body: LoginRequest) -> TokenResponse:
    username = body.username.strip()
    user = db.query(User).filter_by(username=username).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise AppError(
            status_code=401,
            code="INVALID_CREDENTIALS",
            message="Invalid username or password.",
        )
    _ensure_settings(db, user)
    db.commit()
    token = create_access_token(user.id, user.username)
    return TokenResponse(access_token=token, user=_to_user_out(user))


def reset_password(db: Session, body: ResetPasswordRequest) -> ResetPasswordResponse:
    """Set a new password for an existing user (forgot-password flow)."""
    username = body.username.strip()
    user = db.query(User).filter_by(username=username).first()
    if user is None:
        raise AppError(
            status_code=404,
            code="USER_NOT_FOUND",
            message=f"No account found with username '{username}'.",
        )
    if verify_password(body.new_password, user.password_hash):
        raise AppError(
            status_code=400,
            code="PASSWORD_UNCHANGED",
            message="New password must be different from the current password.",
        )

    user.password_hash = hash_password(body.new_password)
    db.commit()
    return ResetPasswordResponse()


def seed_admin_user(db: Session) -> User | None:
    """Create the admin user from env if it does not already exist.

    Requires ADMIN_PASSWORD to be set explicitly — there is no default password.
    """
    username = (settings.admin_username or "").strip()
    password = settings.admin_password or ""
    if not username or not password:
        return None

    existing = db.query(User).filter_by(username=username).first()
    if existing is not None:
        return existing

    user = User(
        username=username,
        email=None,
        password_hash=hash_password(password),
        is_admin=True,
    )
    db.add(user)
    db.flush()
    _ensure_settings(db, user)
    db.commit()
    db.refresh(user)
    return user
