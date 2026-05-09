from datetime import datetime, timedelta

import jwt
from jwt import InvalidTokenError

from ..core.config import settings


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.token_exp_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str):
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except InvalidTokenError:
        return None


def verify_token(token: str):
    payload = decode_access_token(token)
    if payload is None:
        return None
    return payload.get("user")
