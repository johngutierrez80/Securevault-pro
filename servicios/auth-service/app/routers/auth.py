from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from ..dependencies.database import get_db
from ..schemas.user import (
    AuthResponse,
    AuthUser,
    AuthUserWithId,
    PasswordResetConfirm,
    PasswordResetRequest,
    PasswordResetRequestResponse,
    UpdateUserRole,
    UserCreate,
    UserLogin,
)
from ..services.auth_service import (
    authenticate_user,
    build_access_token,
    list_users,
    register_user,
    request_password_reset,
    reset_password,
    update_user_role,
)
from ..utils.jwt import decode_access_token

router = APIRouter()


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    return authorization.split(" ", 1)[1].strip()


def _get_auth_payload(authorization: str | None) -> dict:
    token = _extract_bearer_token(authorization)
    payload = decode_access_token(token)
    if not payload or not payload.get("user"):
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload


def _require_admin(authorization: str | None) -> dict:
    payload = _get_auth_payload(authorization)
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    return payload


@router.post("/register", response_model=AuthResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        created_user = register_user(db, user.email, user.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    access_token = build_access_token(created_user)
    return {
        "access_token": access_token,
        "user": {"email": created_user.email, "role": created_user.role},
    }


@router.post("/login", response_model=AuthResponse)
def login(user: UserLogin, db: Session = Depends(get_db)):
    authenticated_user = authenticate_user(db, user.email, user.password)
    if not authenticated_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = build_access_token(authenticated_user)
    return {
        "access_token": access_token,
        "user": {"email": authenticated_user.email, "role": authenticated_user.role},
    }


@router.get("/me", response_model=AuthUser)
def me(authorization: str | None = Header(default=None)):
    payload = _get_auth_payload(authorization)
    return {"email": payload["user"], "role": payload.get("role", "user")}


@router.get("/users", response_model=list[AuthUserWithId])
def users(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    _require_admin(authorization)
    all_users = list_users(db)
    return [{"id": user.id, "email": user.email, "role": user.role} for user in all_users]


@router.patch("/users/{user_id}/role", response_model=AuthUserWithId)
def patch_user_role(
    user_id: int,
    payload: UpdateUserRole,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth_payload = _require_admin(authorization)
    target_user = update_user_role(db, user_id, payload.role)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent administrators from accidentally removing their own permissions.
    if auth_payload.get("sub") == target_user.id and payload.role != "admin":
        _ = update_user_role(db, user_id, "admin")
        raise HTTPException(
            status_code=400,
            detail="No puedes remover tu propio rol admin desde este endpoint",
        )

    return {"id": target_user.id, "email": target_user.email, "role": target_user.role}


@router.post("/password-reset/request", response_model=PasswordResetRequestResponse)
def password_reset_request(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    try:
        reset_token = request_password_reset(db, payload.email)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not reset_token:
        raise HTTPException(status_code=404, detail="No existe una cuenta con ese correo")

    return {
        "message": "Se generó un token de recuperación para esta versión académica.",
        "reset_token": reset_token,
    }


@router.post("/password-reset/confirm", response_model=dict)
def password_reset_confirm(
    payload: PasswordResetConfirm, db: Session = Depends(get_db)
):
    try:
        updated = reset_password(
            db,
            payload.email,
            payload.reset_token,
            payload.new_password,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not updated:
        raise HTTPException(status_code=404, detail="Token inválido o expirado")

    return {"msg": "Password updated"}
