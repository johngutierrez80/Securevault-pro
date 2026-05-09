import hashlib
import re
import secrets
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from ..core.security import hash_password, verify_password
from ..models.password_reset_token import PasswordResetToken
from ..models.user import User
from ..utils.jwt import create_access_token

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


def register_user(db: Session, email: str, password: str):
    email = validate_email(email)
    password = password.strip()
    password_issues = validate_password_strength(password)
    if password_issues:
        raise ValueError("; ".join(password_issues))
    if db.query(User).filter(User.email == email).first():
        raise ValueError("Ya existe un usuario registrado con ese correo")
    hashed = hash_password(password)
    user = User(email=email, hashed_password=hashed, role="user")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str):
    email = normalize_email(email)
    password = password.strip()
    if not EMAIL_PATTERN.match(email) or not password:
        return None
    user = db.query(User).filter(User.email == email).first()
    if user and verify_password(password, user.hashed_password):
        return user
    return None


def build_access_token(user: User) -> str:
    return create_access_token({"user": user.email, "role": user.role, "sub": str(user.id)})


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
        db.commit()
        return True

    created = register_user(db, normalized_email, password)
    created.role = "admin"
    db.commit()
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
