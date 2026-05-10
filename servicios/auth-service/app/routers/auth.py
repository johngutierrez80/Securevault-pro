from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from ..dependencies.database import get_db
from ..schemas.user import (
    AdminAuditLogResponse,
    AuthResponse,
    AuthSessionResponse,
    AuthUser,
    AuthUserWithId,
    PasswordResetConfirm,
    PasswordResetRequest,
    PasswordResetRequestResponse,
    SessionValidationResponse,
    UpdateUserRole,
    UpdateUserStatus,
    UserCreate,
    UserLogin,
)
from ..services.auth_service import (
    authenticate_user,
    build_access_token,
    get_user_by_id,
    get_user_from_token,
    list_active_sessions,
    list_active_users_with_sessions,
    list_admin_audit_logs,
    list_users,
    revoke_sessions_for_user,
    register_user,
    request_password_reset,
    reset_password,
    update_user_role,
    update_user_status,
    write_admin_audit_log,
)

router = APIRouter()


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    return authorization.split(" ", 1)[1].strip()


def _get_auth_payload(authorization: str | None, db: Session) -> tuple[dict, object]:
    token = _extract_bearer_token(authorization)
    authenticated_user, payload = get_user_from_token(db, token)
    if not payload or not authenticated_user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload, authenticated_user


def _require_admin(authorization: str | None, db: Session) -> tuple[dict, object]:
    payload, authenticated_user = _get_auth_payload(authorization, db)
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    return payload, authenticated_user


@router.post("/register", response_model=AuthResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        created_user = register_user(db, user.email, user.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    access_token = build_access_token(created_user, db)
    return {
        "access_token": access_token,
        "user": {
            "email": created_user.email,
            "role": created_user.role,
            "is_active": created_user.is_active,
        },
    }


@router.post("/login", response_model=AuthResponse)
def login(user: UserLogin, db: Session = Depends(get_db)):
    authenticated_user = authenticate_user(db, user.email, user.password)
    if not authenticated_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = build_access_token(authenticated_user, db)
    return {
        "access_token": access_token,
        "user": {
            "email": authenticated_user.email,
            "role": authenticated_user.role,
            "is_active": authenticated_user.is_active,
        },
    }


@router.get("/me", response_model=AuthUser)
def me(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    payload, authenticated_user = _get_auth_payload(authorization, db)
    return {
        "email": payload["user"],
        "role": payload.get("role", "user"),
        "is_active": authenticated_user.is_active,
    }


@router.get("/session/validate", response_model=SessionValidationResponse)
def validate_session(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    payload, authenticated_user = _get_auth_payload(authorization, db)
    return {
        "email": payload["user"],
        "role": payload.get("role", "user"),
        "is_active": authenticated_user.is_active,
    }


@router.get("/users", response_model=list[AuthUserWithId])
def users(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    _require_admin(authorization, db)
    all_users = list_users(db)
    return [
        {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
        }
        for user in all_users
    ]


@router.patch("/users/{user_id}/role", response_model=AuthUserWithId)
def patch_user_role(
    user_id: int,
    payload: UpdateUserRole,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth_payload, actor_user = _require_admin(authorization, db)
    target_user = update_user_role(db, user_id, payload.role)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent administrators from accidentally removing their own permissions.
    if auth_payload.get("sub") == str(target_user.id) and payload.role != "admin":
        _ = update_user_role(db, user_id, "admin")
        raise HTTPException(
            status_code=400,
            detail="No puedes remover tu propio rol admin desde este endpoint",
        )

    write_admin_audit_log(
        db,
        actor_user=actor_user,
        action="update_user_role",
        target_user=target_user,
        details=f"Nuevo rol: {target_user.role}",
    )

    return {
        "id": target_user.id,
        "email": target_user.email,
        "role": target_user.role,
        "is_active": target_user.is_active,
    }


@router.patch("/users/{user_id}/status", response_model=AuthUserWithId)
def patch_user_status(
    user_id: int,
    payload: UpdateUserStatus,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth_payload, actor_user = _require_admin(authorization, db)

    target_user = get_user_by_id(db, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    if auth_payload.get("sub") == str(target_user.id) and payload.is_active is False:
        raise HTTPException(status_code=400, detail="No puedes desactivar tu propia cuenta")

    updated_user = update_user_status(db, user_id, payload.is_active)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.is_active is False:
        _ = revoke_sessions_for_user(db, user_id)

    write_admin_audit_log(
        db,
        actor_user=actor_user,
        action="update_user_status",
        target_user=updated_user,
        details=f"Estado activo: {updated_user.is_active}",
    )

    return {
        "id": updated_user.id,
        "email": updated_user.email,
        "role": updated_user.role,
        "is_active": updated_user.is_active,
    }


@router.get("/users/{user_id}/sessions", response_model=list[AuthSessionResponse])
def get_user_sessions(
    user_id: int,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    _require_admin(authorization, db)
    target_user = get_user_by_id(db, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    sessions = list_active_sessions(db, user_id=user_id)
    return [
        {
            "id": session.id,
            "user_id": session.user_id,
            "token_jti": session.token_jti,
            "issued_at": session.issued_at.isoformat(),
            "expires_at": session.expires_at.isoformat(),
        }
        for session in sessions
    ]


@router.post("/users/{user_id}/sessions/revoke", response_model=dict)
def revoke_user_sessions(
    user_id: int,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    _auth_payload, actor_user = _require_admin(authorization, db)
    target_user = get_user_by_id(db, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    revoked_count = revoke_sessions_for_user(db, user_id)

    write_admin_audit_log(
        db,
        actor_user=actor_user,
        action="revoke_user_sessions",
        target_user=target_user,
        details=f"Sesiones revocadas: {revoked_count}",
    )

    return {"revoked": revoked_count}


@router.get("/admin/audit-logs", response_model=list[AdminAuditLogResponse])
def admin_audit_logs(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    _require_admin(authorization, db)
    logs = list_admin_audit_logs(db, limit=150)
    return [
        {
            "id": log.id,
            "actor_user_id": log.actor_user_id,
            "actor_email": log.actor_email,
            "action": log.action,
            "target_user_id": log.target_user_id,
            "target_email": log.target_email,
            "details": log.details,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]


@router.get("/admin/active-users", response_model=list[dict])
def admin_active_users(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    _require_admin(authorization, db)
    active_users = list_active_users_with_sessions(db)
    return active_users


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
