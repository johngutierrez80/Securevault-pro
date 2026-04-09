from app.core.security import hash_password, verify_password
from app.utils.jwt import create_access_token, verify_token


def test_hash_and_verify_password_roundtrip():
    password = "super-secret-password"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_passwords_longer_than_72_bytes_are_normalized_consistently():
    base = "a" * 72
    password_a = base + "first-suffix"
    password_b = base + "second-suffix"

    hashed = hash_password(password_a)

    assert verify_password(password_b, hashed) is True


def test_create_and_verify_access_token_returns_username():
    token = create_access_token({"user": "alice"})

    assert verify_token(token) == "alice"


def test_verify_token_returns_none_for_invalid_token():
    assert verify_token("not-a-valid-token") is None
