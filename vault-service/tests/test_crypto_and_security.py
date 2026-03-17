import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt

from app.core.config import settings
from app.core.security import verify_token
from app.utils.crypto import encrypt, decrypt


def test_encrypt_and_decrypt_roundtrip():
    plaintext = "my-ultra-secret-password"
    encrypted = encrypt(plaintext)

    assert encrypted != plaintext
    assert decrypt(encrypted) == plaintext


def test_verify_token_returns_username_from_valid_jwt():
    token = jwt.encode({"user": "alice"}, settings.secret_key, algorithm=settings.algorithm)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    assert verify_token(credentials) == "alice"


def test_verify_token_raises_for_invalid_jwt():
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid-token")

    with pytest.raises(HTTPException) as exc_info:
        verify_token(credentials)

    assert exc_info.value.status_code == 401
