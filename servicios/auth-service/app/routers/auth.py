from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from ..dependencies.database import get_db
from ..schemas.user import (
    AdminAuditLogResponse,
    AuthResponse,
    AuthSessionResponse,
    AuthUser,
    AuthUserWithId,
    EmailVerificationRequest,
    EmailVerificationResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    PasswordResetRequestResponse,
    ResendVerificationEmailRequest,
    ResendVerificationEmailResponse,
    SessionValidationResponse,
    UpdateUserRole,
    UpdateUserStatus,
    UserCreate,
    UserLogin,
)
from ..services.auth_service import (
    authenticate_user,
    build_access_token,
    confirm_email,
    generate_email_verification_token,
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
from ..utils.email_service import send_reset_email, send_verification_email, validate_email_domain

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


@router.post("/register", response_model=dict)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # Validar dominio antes de crear la cuenta
    domain_valid = await validate_email_domain(user.email)
    if not domain_valid:
        raise HTTPException(
            status_code=400,
            detail="El dominio del correo no existe o no acepta emails. Verifica la dirección ingresada."
        )

    try:
        created_user, verification_token = register_user(db, user.email, user.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Flujo con verificación: created_user es None hasta confirmar el correo
    if verification_token:
        email_sent = await send_verification_email(user.email, verification_token)
        return {
            "message": "Por favor verifica tu correo para activar tu cuenta",
            "email_verified": False,
            "requires_verification": True,
            "email_verification_sent": email_sent,
        }

    # Flujo sin verificación: usuario creado directamente
    access_token = build_access_token(created_user, db)
    return {
        "message": "Usuario registrado correctamente",
        "email_verified": True,
        "requires_verification": False,
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "email": created_user.email,
            "role": created_user.role,
            "is_active": created_user.is_active,
        },
    }


@router.post("/login", response_model=AuthResponse)
async def login(user: UserLogin, db: Session = Depends(get_db)):
    from ..models.user import User
    from ..services.auth_service import normalize_email
    from ..core.config import redis_client

    normalized_email = normalize_email(user.email)
    fail_key = f"login_fail:{normalized_email}"
    MAX_ATTEMPTS = 3
    LOCKOUT_TTL = 300  # 5 minutos

    # Verificar si la cuenta está bloqueada
    try:
        fail_count = int(redis_client.get(fail_key) or 0) if redis_client else 0
    except Exception:
        fail_count = 0

    if fail_count >= MAX_ATTEMPTS:
        raise HTTPException(
            status_code=423,
            detail="Cuenta bloqueada por múltiples intentos fallidos. Revisa tu correo para restablecer tu contraseña.",
        )

    authenticated_user = authenticate_user(db, user.email, user.password)
    if not authenticated_user:
        from ..models.email_verification_token import EmailVerificationToken
        # Verificar si hay un registro pendiente de confirmación (flujo nuevo)
        pending = (
            db.query(EmailVerificationToken)
            .filter(
                EmailVerificationToken.email == normalized_email,
                EmailVerificationToken.confirmed_at.is_(None),
                EmailVerificationToken.hashed_password.isnot(None),
            )
            .first()
        )
        if pending:
            raise HTTPException(
                status_code=403,
                detail="Tu correo no ha sido verificado. Revisa tu bandeja de entrada."
            )
        # Verificar también usuarios no verificados del flujo antiguo
        existing_user = db.query(User).filter(User.email == normalized_email).first()
        if existing_user and not existing_user.email_verified:
            raise HTTPException(
                status_code=403,
                detail="Tu correo no ha sido verificado. Revisa tu bandeja de entrada."
            )

        # Incrementar contador de intentos fallidos
        try:
            if redis_client:
                new_count = redis_client.incr(fail_key)
                redis_client.expire(fail_key, LOCKOUT_TTL)

                # En el 3er intento fallido: enviar email de recuperación automáticamente
                if new_count >= MAX_ATTEMPTS and existing_user:
                    reset_token = request_password_reset(db, normalized_email)
                    if reset_token:
                        await send_reset_email(normalized_email, reset_token, locked_out=True)
                    raise HTTPException(
                        status_code=423,
                        detail="Cuenta bloqueada por múltiples intentos fallidos. Revisa tu correo para restablecer tu contraseña.",
                    )
        except HTTPException:
            raise
        except Exception:
            pass

        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Login exitoso: limpiar contador de fallos
    try:
        if redis_client:
            redis_client.delete(fail_key)
    except Exception:
        pass

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


@router.delete("/users/{user_id}", response_model=dict)
def delete_user(
    user_id: int,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth_payload, actor_user = _require_admin(authorization, db)

    target_user = get_user_by_id(db, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if auth_payload.get("sub") == str(target_user.id):
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propia cuenta")

    if target_user.role == "admin":
        raise HTTPException(status_code=400, detail="No puedes eliminar una cuenta admin")

    write_admin_audit_log(
        db,
        actor_user=actor_user,
        action="delete_user",
        target_user=target_user,
        details=f"Usuario eliminado: {target_user.email}",
    )

    db.delete(target_user)
    db.commit()

    return {"message": f"Usuario {target_user.email} eliminado correctamente"}


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
async def password_reset_request(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    try:
        reset_token = request_password_reset(db, payload.email)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not reset_token:
        raise HTTPException(status_code=404, detail="No existe una cuenta con ese correo")

    await send_reset_email(payload.email, reset_token)

    return {
        "message": "Te enviamos un correo con instrucciones para recuperar tu contraseña.",
        "reset_token": None,
    }


@router.post("/password-reset/confirm", response_model=dict)
def password_reset_confirm(
    payload: PasswordResetConfirm, db: Session = Depends(get_db)
):
    from ..core.config import redis_client
    from ..services.auth_service import normalize_email

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

    # Limpiar el contador de intentos fallidos en Redis para desbloquear la cuenta
    try:
        if redis_client:
            normalized_email = normalize_email(payload.email)
            redis_client.delete(f"login_fail:{normalized_email}")
    except Exception:
        pass

    return {"msg": "Password updated"}


@router.post("/confirm-email", response_model=EmailVerificationResponse)
def confirm_email_endpoint(
    payload: EmailVerificationRequest, db: Session = Depends(get_db)
):
    try:
        verified = confirm_email(db, payload.email, payload.verification_token)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not verified:
        raise HTTPException(status_code=400, detail="Token de verificación inválido o expirado")

    return {"message": "Correo verificado correctamente. Ya puedes iniciar sesión."}


@router.post("/resend-verification-email", response_model=ResendVerificationEmailResponse)
async def resend_verification_email(
    payload: ResendVerificationEmailRequest, db: Session = Depends(get_db)
):
    try:
        verification_token = generate_email_verification_token(db, payload.email)
    except ValueError as exc:
        # No revelar si existe el usuario o no
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if verification_token:
        await send_verification_email(payload.email, verification_token)

    return {
        "message": "Si existe una cuenta con ese correo, recibirás un email de verificación."
    }

