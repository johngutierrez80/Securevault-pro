from sqlalchemy.orm import Session

from ..core.security import hash_password, verify_password
from ..models.user import User
from ..utils.jwt import create_access_token


def register_user(db: Session, username: str, password: str):
    username = username.strip()
    password = password.strip()
    if not username or not password:
        return None
    if db.query(User).filter(User.username == username).first():
        return None
    hashed = hash_password(password)
    user = User(username=username, hashed_password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str):
    username = username.strip()
    password = password.strip()
    if not username or not password:
        return None
    user = db.query(User).filter(User.username == username).first()
    if user and verify_password(password, user.hashed_password):
        return create_access_token({"user": username})
    return None
