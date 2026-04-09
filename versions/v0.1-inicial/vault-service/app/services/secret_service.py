from sqlalchemy.orm import Session
from ..models.secret import Secret
from ..utils.crypto import encrypt, decrypt


def save_secret(db: Session, site: str, password: str, owner: str):
    enc = encrypt(password)
    secret = Secret(site=site, encrypted_password=enc, owner=owner)
    db.add(secret)
    db.commit()
    db.refresh(secret)
    return secret


def get_secrets(db: Session, owner: str):
    secrets = db.query(Secret).filter(Secret.owner == owner).all()
    return [{"id": s.id, "site": s.site, "password": decrypt(s.encrypted_password)} for s in secrets]


def get_secret(db: Session, owner: str, secret_id: int):
    return db.query(Secret).filter(Secret.owner == owner, Secret.id == secret_id).first()


def update_secret(db: Session, secret_id: int, owner: str, site: str, password: str):
    secret = get_secret(db, owner, secret_id)
    if not secret:
        return None
    secret.site = site
    secret.encrypted_password = encrypt(password)
    db.commit()
    db.refresh(secret)
    return secret


def delete_secret(db: Session, secret_id: int, owner: str):
    secret = get_secret(db, owner, secret_id)
    if not secret:
        return False
    db.delete(secret)
    db.commit()
    return True