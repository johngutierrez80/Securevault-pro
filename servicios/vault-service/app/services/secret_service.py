from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from ..models.secret import Secret
from ..utils.job_queue import clear_secret_expiration
from ..utils.job_queue import enqueue_security_event
from ..utils.job_queue import schedule_secret_expiration
from ..utils.crypto import decrypt, encrypt


def save_secret(
    db: Session,
    site: str,
    password: str,
    owner: str,
    expires_in_days: int | None = None,
):
    enc = encrypt(password)
    secret = Secret(site=site, encrypted_password=enc, owner=owner)
    db.add(secret)
    db.commit()
    db.refresh(secret)

    if expires_in_days is not None:
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
        schedule_secret_expiration(secret.id, owner, int(expires_at.timestamp()))

    enqueue_security_event("secret_saved", owner, site, {"secret_id": secret.id})
    return secret


def get_secrets(db: Session, owner: str):
    secrets = db.query(Secret).filter(Secret.owner == owner).all()
    return [
        {"id": s.id, "site": s.site, "password": decrypt(s.encrypted_password)}
        for s in secrets
    ]


def get_secret(db: Session, owner: str, secret_id: int):
    return (
        db.query(Secret).filter(Secret.owner == owner, Secret.id == secret_id).first()
    )


def update_secret(
    db: Session,
    secret_id: int,
    owner: str,
    site: str,
    password: str,
    expires_in_days: int | None = None,
):
    secret = get_secret(db, owner, secret_id)
    if not secret:
        return None
    secret.site = site
    secret.encrypted_password = encrypt(password)
    db.commit()
    db.refresh(secret)

    if expires_in_days is not None:
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
        schedule_secret_expiration(secret.id, owner, int(expires_at.timestamp()))

    enqueue_security_event("secret_updated", owner, site, {"secret_id": secret.id})
    return secret


def delete_secret(db: Session, secret_id: int, owner: str):
    secret = get_secret(db, owner, secret_id)
    if not secret:
        return False
    site = secret.site
    db.delete(secret)
    db.commit()

    clear_secret_expiration(secret_id, owner)
    enqueue_security_event("secret_deleted", owner, site, {"secret_id": secret_id})
    return True
