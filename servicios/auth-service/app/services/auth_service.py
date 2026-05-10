import hashlib
import re
import secrets
from uuid import uuid4
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.security import hash_password, verify_password
from ..models.admin_audit_log import AdminAuditLog
from ..models.auth_session import AuthSession
from ..models.email_verification_token import EmailVerificationToken
from ..models.password_reset_token import PasswordResetToken
from ..models.user import User
from ..utils.jwt import create_access_token, decode_access_token
from ..utils.email_service import validate_email_domain, send_verification_email

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PASSWORD_MIN_LENGTH = 10
PASSWORD_RESET_TOKEN_MINUTES = 15
VALID_ROLES = {"admin", "user"}


def normalize_email(email: str) -> str:
    return email.strip().lower()


def validate_email(email: str) -> str:
    normalized = normalize_email(email)
    if not EMAIL_PATTERN.match(normalized):
        raise ValueError("Ingresa un correo electrónico válido")
    return normalized


def validate_password_strength(password: str) -> list[str]:
    issues: list[str] = []
    candidate = password.strip()
    if len(candidate) < PASSWORD_MIN_LENGTH:
        issues.append(f"La contraseña debe tener al menos {PASSWORD_MIN_LENGTH} caracteres")
    if len(candidate.encode("utf-8")) > 72:
        issues.append("La contraseña no debe superar 72 bytes por compatibilidad con bcrypt")
    if not re.search(r"[a-z]", candidate):
        issues.append("Debe incluir una letra minúscula")
    if not re.search(r"[A-Z]", candidate):
        issues.append("Debe incluir una letra mayúscula")
    if not re.search(r"\d", candidate):
        issues.append("Debe incluir al menos un número")
    if not re.search(r"[^A-Za-z0-9]", candidate):
        issues.append("Debe incluir al menos un símbolo")
    return issues


def register_user(db: Session, email: str, password: str) -> tuple[User | None, str | None]:
    """
    Registra un nuevo usuario.

    Si REQUIRE_EMAIL_VERIFICATION está activo:
        - NO crea el usuario en la tabla `users` todavía.
        - Almacena un registro pendiente (con hashed_password) en `email_verification_tokens`.
        - El usuario se crea definitivamente solo cuando confirma el correo.
        - Retorna (None, token).

    Si la verificación está desactivada:
        - Crea el usuario directamente.
        - Retorna (user, None).
    """
    email = validate_email(email)
    password = password.strip()
    password_issues = validate_password_strength(password)
    if password_issues:
        raise ValueError("; ".join(password_issues))

    # Verificar si ya existe un usuario VERIFICADO con este correo
    existing_verified = (
        db.query(User)
        .filter(User.email == email, User.email_verified == True)  # noqa: E712
        .first()
    )
    if existing_verified:
        raise ValueError("Ya existe un usuario registrado con ese correo")

    hashed = hash_password(password)

    if not settings.require_email_verification:
        # Sin verificación: crear usuario directamente
        # Eliminar usuarios no verificados previos para el mismo correo
        db.query(User).filter(User.email == email, User.email_verified == False).delete(  # noqa: E712
            synchronize_session=False
        )
        user = User(
            email=email,
            hashed_password=hashed,
            role="user",
            is_active=True,
            email_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user, None

    # Con verificación: solo guardar registro pendiente en la tabla de tokens
    # Limpiar tokens pendientes anteriores (y cualquier usuario no verificado del flujo antiguo)
    db.query(EmailVerificationToken).filter(
        EmailVerificationToken.email == email,
        EmailVerificationToken.confirmed_at.is_(None),
    ).delete(synchronize_session=False)
    db.query(User).filter(User.email == email, User.email_verified == False).delete(  # noqa: E712
        synchronize_session=False
    )

    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    verification_record = EmailVerificationToken(
        email=email,
        token_hash=token_hash,
        hashed_password=hashed,
        expires_at=datetime.utcnow() + timedelta(minutes=settings.email_verification_minutes),
    )
    db.add(verification_record)
    db.commit()
    # El usuario NO existe todavía — se crea en confirm_email
    return None, token


def authenticate_user(db: Session, email: str, password: str):
    email = normalize_email(email)
    password = password.strip()
    if not EMAIL_PATTERN.match(email) or not password:
        return None
    user = db.query(User).filter(User.email == email).first()
    if user and user.is_active and verify_password(password, user.hashed_password):
        # Verificar si el email está verificado
        if settings.require_email_verification and not user.email_verified:
            return None  # Email no verificado
        return user
    return None


def build_access_token(user: User, db: Session | None = None) -> str:
    session_jti = str(uuid4())
    exp_minutes = (
        settings.admin_token_exp_minutes if user.role == "admin"
        else settings.token_exp_minutes
    )
    token = create_access_token(
        {
            "user": user.email,
            "role": user.role,
            "sub": str(user.id),
            "jti": session_jti,
        },
        exp_minutes=exp_minutes,
    )

    if db is not None:
        payload = decode_access_token(token) or {}
        exp_ts = payload.get("exp")
        if isinstance(exp_ts, (int, float)):
            expires_at = datetime.utcfromtimestamp(exp_ts)
        else:
            expires_at = datetime.utcnow() + timedelta(minutes=settings.token_exp_minutes)

        db.add(
            AuthSession(
                user_id=user.id,
                token_jti=session_jti,
                issued_at=datetime.utcnow(),
                expires_at=expires_at,
            )
        )
        db.commit()

    return token


def list_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.id.asc()).all()


def update_user_role(db: Session, user_id: int, role: str) -> User | None:
    normalized_role = role.strip().lower()
    if normalized_role not in VALID_ROLES:
        raise ValueError("Rol inválido. Usa 'admin' o 'user'")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    user.role = normalized_role
    db.commit()
    db.refresh(user)
    return user


def update_user_status(db: Session, user_id: int, is_active: bool) -> User | None:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    user.is_active = bool(is_active)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def get_user_from_token(db: Session, token: str) -> tuple[User | None, dict | None]:
    payload = decode_access_token(token)
    if not payload:
        return None, None

    subject = payload.get("sub")
    email = normalize_email(payload.get("user", ""))
    session_jti = payload.get("jti")
    if not subject or not email or not session_jti:
        return None, None

    try:
        user_id = int(subject)
    except (TypeError, ValueError):
        return None, None

    user = db.query(User).filter(User.id == user_id, User.email == email).first()
    if not user or not user.is_active:
        return None, None

    session = (
        db.query(AuthSession)
        .filter(
            AuthSession.token_jti == session_jti,
            AuthSession.user_id == user.id,
            AuthSession.revoked_at.is_(None),
        )
        .first()
    )
    if not session or session.expires_at < datetime.utcnow():
        return None, None

    return user, payload


def list_active_sessions(db: Session, user_id: int | None = None) -> list[AuthSession]:
    query = db.query(AuthSession).filter(
        AuthSession.revoked_at.is_(None),
        AuthSession.expires_at >= datetime.utcnow(),
    )
    if user_id is not None:
        query = query.filter(AuthSession.user_id == user_id)
    return query.order_by(AuthSession.issued_at.desc()).all()


def revoke_sessions_for_user(db: Session, user_id: int) -> int:
    now = datetime.utcnow()
    updated = (
        db.query(AuthSession)
        .filter(
            AuthSession.user_id == user_id,
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at >= now,
        )
        .update({AuthSession.revoked_at: now}, synchronize_session=False)
    )
    db.commit()
    return int(updated)


def write_admin_audit_log(
    db: Session,
    actor_user: User,
    action: str,
    target_user: User | None = None,
    details: str | None = None,
) -> AdminAuditLog:
    entry = AdminAuditLog(
        actor_user_id=actor_user.id,
        actor_email=actor_user.email,
        action=action,
        target_user_id=target_user.id if target_user else None,
        target_email=target_user.email if target_user else None,
        details=details,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_admin_audit_logs(db: Session, limit: int = 100) -> list[AdminAuditLog]:
    safe_limit = min(max(limit, 1), 500)
    return db.query(AdminAuditLog).order_by(AdminAuditLog.created_at.desc()).limit(safe_limit).all()


def list_active_users_with_sessions(db: Session) -> list[dict]:
    active_sessions = list_active_sessions(db)
    user_ids = {session.user_id for session in active_sessions}

    if not user_ids:
        return []

    users = db.query(User).filter(User.id.in_(user_ids)).all()
    result = []
    for user in users:
        session_count = sum(1 for s in active_sessions if s.user_id == user.id)
        result.append(
            {
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active,
                "active_session_count": session_count,
            }
        )
    return sorted(result, key=lambda x: x["active_session_count"], reverse=True)


def bootstrap_initial_admin(db: Session, email: str | None, password: str | None) -> bool:
    if not email or not password:
        return False

    normalized_email = normalize_email(email)
    if not normalized_email or not password.strip():
        return False

    existing_admin = db.query(User).filter(User.role == "admin").first()
    if existing_admin:
        return False

    user = db.query(User).filter(User.email == normalized_email).first()
    if user:
        user.role = "admin"
        user.email_verified = True  # Bootstrap admin no requiere verificación
        db.commit()
        return True

    # Crear admin con email ya verificado (no pasa por flujo de registro normal)
    hashed = hash_password(password.strip())
    admin_user = User(
        email=normalized_email,
        hashed_password=hashed,
        role="admin",
        is_active=True,
        email_verified=True,
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    return True


def request_password_reset(db: Session, email: str):
    email = normalize_email(email)
    if not EMAIL_PATTERN.match(email):
        raise ValueError("Ingresa un correo electrónico válido")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None

    db.query(PasswordResetToken).filter(
        PasswordResetToken.email == email,
        PasswordResetToken.consumed_at.is_(None),
    ).delete(synchronize_session=False)

    reset_token = secrets.token_urlsafe(32)
    reset_record = PasswordResetToken(
        email=email,
        token_hash=hashlib.sha256(reset_token.encode("utf-8")).hexdigest(),
        expires_at=datetime.utcnow() + timedelta(minutes=PASSWORD_RESET_TOKEN_MINUTES),
    )
    db.add(reset_record)
    db.commit()
    return reset_token


def reset_password(db: Session, email: str, reset_token: str, new_password: str):
    email = normalize_email(email)
    if not EMAIL_PATTERN.match(email):
        raise ValueError("Ingresa un correo electrónico válido")

    password_issues = validate_password_strength(new_password)
    if password_issues:
        raise ValueError("; ".join(password_issues))

    token_hash = hashlib.sha256(reset_token.encode("utf-8")).hexdigest()
    token_record = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.email == email,
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.consumed_at.is_(None),
        )
        .first()
    )
    if not token_record:
        return False
    if token_record.expires_at < datetime.utcnow():
        db.delete(token_record)
        db.commit()
        return False

    user = db.query(User).filter(User.email == email).first()
    if not user:
        return False

    user.hashed_password = hash_password(new_password)
    token_record.consumed_at = datetime.utcnow()
    db.commit()
    return True


def generate_email_verification_token(db: Session, email: str) -> str | None:
    """
    Genera un nuevo token de verificación para un correo pendiente de confirmación.

    Busca primero en la tabla de tokens (registro pendiente del flujo nuevo),
    luego en `users` (flujo antiguo con email_verified=False).
    Retorna None silenciosamente si no hay registro pendiente (no revela si el correo existe).
    """
    email = normalize_email(email)
    if not EMAIL_PATTERN.match(email):
        raise ValueError("Ingresa un correo electrónico válido")

    # ¿Ya existe y está verificado?
    user = db.query(User).filter(User.email == email).first()
    if user and user.email_verified:
        raise ValueError("Este correo ya está verificado")

    # Buscar registro pendiente (flujo nuevo) para recuperar la contraseña hasheada
    pending_token = (
        db.query(EmailVerificationToken)
        .filter(
            EmailVerificationToken.email == email,
            EmailVerificationToken.confirmed_at.is_(None),
        )
        .first()
    )

    # Determinar qué contraseña hasheada conservar
    if pending_token and pending_token.hashed_password:
        saved_hashed_password = pending_token.hashed_password
    elif user:
        saved_hashed_password = user.hashed_password  # flujo antiguo
    else:
        # No hay registro pendiente ni usuario → no revelar nada
        return None

    # Limpiar tokens anteriores
    db.query(EmailVerificationToken).filter(
        EmailVerificationToken.email == email,
        EmailVerificationToken.confirmed_at.is_(None),
    ).delete(synchronize_session=False)

    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    verification_record = EmailVerificationToken(
        email=email,
        token_hash=token_hash,
        hashed_password=saved_hashed_password,
        expires_at=datetime.utcnow() + timedelta(minutes=settings.email_verification_minutes),
    )
    db.add(verification_record)
    db.commit()
    return token


def confirm_email(db: Session, email: str, verification_token: str) -> bool:
    """
    Confirma el correo y crea el usuario si aún no existe.

    Flujo nuevo: el token incluye `hashed_password` → se crea el User aquí.
    Flujo antiguo (compat): el token no tiene `hashed_password` → el User ya existe, solo se marca.
    """
    email = normalize_email(email)
    if not EMAIL_PATTERN.match(email):
        raise ValueError("Ingresa un correo electrónico válido")

    token_hash = hashlib.sha256(verification_token.encode("utf-8")).hexdigest()
    token_record = (
        db.query(EmailVerificationToken)
        .filter(
            EmailVerificationToken.email == email,
            EmailVerificationToken.token_hash == token_hash,
            EmailVerificationToken.confirmed_at.is_(None),
        )
        .first()
    )

    if not token_record:
        return False

    if token_record.expires_at < datetime.utcnow():
        db.delete(token_record)
        db.commit()
        return False

    # Flujo nuevo: el token tiene la contraseña hasheada → crear el usuario ahora
    if token_record.hashed_password:
        existing = db.query(User).filter(User.email == email).first()
        if not existing:
            user = User(
                email=email,
                hashed_password=token_record.hashed_password,
                role="user",
                is_active=True,
                email_verified=True,
            )
            db.add(user)
        else:
            # Ya existe (edge case): actualizar contraseña y marcar verificado
            existing.hashed_password = token_record.hashed_password
            existing.email_verified = True
    else:
        # Flujo antiguo: usuario ya existe en la tabla users, solo marcar verificado
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return False
        user.email_verified = True

    token_record.confirmed_at = datetime.utcnow()
    db.commit()
    return True

