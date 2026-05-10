import re
from typing import Annotated

from pydantic import BaseModel, StringConstraints, field_validator

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

EmailStr = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)
]
PasswordStr = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=72)
]


class UserCreate(BaseModel):
    email: EmailStr
    password: PasswordStr

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not EMAIL_PATTERN.match(normalized):
            raise ValueError("Ingresa un correo electrónico válido")
        return normalized


class UserLogin(BaseModel):
    email: EmailStr
    password: PasswordStr

    @field_validator("email")
    @classmethod
    def validate_login_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not EMAIL_PATTERN.match(normalized):
            raise ValueError("Ingresa un correo electrónico válido")
        return normalized


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthUser(BaseModel):
    email: str
    role: str
    is_active: bool = True


class AuthUserWithId(AuthUser):
    id: int


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUser


class PasswordResetRequest(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def validate_reset_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not EMAIL_PATTERN.match(normalized):
            raise ValueError("Ingresa un correo electrónico válido")
        return normalized


class PasswordResetRequestResponse(BaseModel):
    message: str
    reset_token: str | None = None


class PasswordResetConfirm(BaseModel):
    email: EmailStr
    reset_token: str
    new_password: PasswordStr

    @field_validator("email")
    @classmethod
    def validate_confirm_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not EMAIL_PATTERN.match(normalized):
            raise ValueError("Ingresa un correo electrónico válido")
        return normalized


class UpdateUserRole(BaseModel):
    role: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"admin", "user"}:
            raise ValueError("Rol inválido. Usa 'admin' o 'user'")
        return normalized


class UpdateUserStatus(BaseModel):
    is_active: bool


class SessionValidationResponse(BaseModel):
    email: str
    role: str
    is_active: bool


class AuthSessionResponse(BaseModel):
    id: int
    user_id: int
    token_jti: str
    issued_at: str
    expires_at: str


class AdminAuditLogResponse(BaseModel):
    id: int
    actor_user_id: int
    actor_email: str
    action: str
    target_user_id: int | None = None
    target_email: str | None = None
    details: str | None = None
    created_at: str
