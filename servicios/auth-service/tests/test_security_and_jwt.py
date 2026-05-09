from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password, verify_password
from app.models.password_reset_token import PasswordResetToken
from app.models.user import Base, User
from app.services.auth_service import (
    authenticate_user,
    bootstrap_initial_admin,
    build_access_token,
    list_users,
    register_user,
    request_password_reset,
    reset_password,
    update_user_role,
    validate_password_strength,
)
from app.utils.jwt import create_access_token, verify_token


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def setup_module(module):
    del module
    Base.metadata.create_all(bind=engine)


def teardown_function(function):
    del function
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


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
    token = create_access_token({"user": "alice@example.com", "role": "user"})

    assert verify_token(token) == "alice@example.com"


def test_verify_token_returns_none_for_invalid_token():
    assert verify_token("not-a-valid-token") is None


def test_password_strength_validator_reports_missing_requirements():
    issues = validate_password_strength("weak")

    assert any("al menos" in issue for issue in issues)
    assert any("mayúscula" in issue for issue in issues)
    assert any("número" in issue for issue in issues)
    assert any("símbolo" in issue for issue in issues)


def test_register_login_and_password_reset_flow():
    db = TestingSessionLocal()
    try:
        user = register_user(db, "alice@example.com", "StrongPass1!")

        assert user.email == "alice@example.com"
        assert user.role == "user"
        assert authenticate_user(db, "alice@example.com", "StrongPass1!") is not None

        reset_token = request_password_reset(db, "alice@example.com")
        assert reset_token

        assert reset_password(db, "alice@example.com", reset_token, "NewStrongPass2$") is True
        assert authenticate_user(db, "alice@example.com", "NewStrongPass2$") is not None
    finally:
        db.close()


def test_admin_role_management_flow():
    db = TestingSessionLocal()
    try:
        user_a = register_user(db, "admin@example.com", "StrongPass1!")
        user_b = register_user(db, "user@example.com", "StrongPass1!")

        promoted = update_user_role(db, user_a.id, "admin")
        assert promoted is not None
        assert promoted.role == "admin"

        all_users = list_users(db)
        assert len(all_users) == 2
        assert {u.email for u in all_users} == {"admin@example.com", "user@example.com"}

        demoted = update_user_role(db, user_b.id, "user")
        assert demoted is not None
        assert demoted.role == "user"
    finally:
        db.close()


def test_bootstrap_initial_admin_creates_admin_once():
    db = TestingSessionLocal()
    try:
        created = bootstrap_initial_admin(db, "boot@example.com", "StrongPass1!")
        assert created is True

        user = db.query(User).filter(User.email == "boot@example.com").first()
        assert user is not None
        assert user.role == "admin"

        skipped = bootstrap_initial_admin(db, "other@example.com", "StrongPass1!")
        assert skipped is False
    finally:
        db.close()
