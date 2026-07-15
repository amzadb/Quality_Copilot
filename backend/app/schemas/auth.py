from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    email: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class ResetPasswordRequest(BaseModel):
    """Forgot-password style reset — username + new password only."""

    username: str = Field(min_length=3, max_length=64)
    new_password: str = Field(min_length=6, max_length=128)


class ResetPasswordResponse(BaseModel):
    ok: bool = True
    message: str = "Password updated successfully."


class UserOut(BaseModel):
    id: UUID
    username: str
    email: str | None = None
    is_admin: bool = False
    created_at: datetime | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
