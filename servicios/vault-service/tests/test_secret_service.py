from unittest.mock import patch

from app.models.secret import Base
from app.services.secret_service import (
    delete_secret,
    get_secrets,
    save_secret,
    update_secret,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def build_test_db():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return TestingSessionLocal()


def test_save_and_get_secrets_returns_decrypted_password():
    db = build_test_db()

    save_secret(db, "github.com", "p@ssw0rd", "alice")
    secrets = get_secrets(db, "alice")

    assert len(secrets) == 1
    assert secrets[0]["site"] == "github.com"
    assert secrets[0]["password"] == "p@ssw0rd"


def test_update_secret_changes_site_and_password():
    db = build_test_db()
    secret = save_secret(db, "github.com", "old-password", "alice")

    updated = update_secret(db, secret.id, "alice", "gitlab.com", "new-password")
    secrets = get_secrets(db, "alice")

    assert updated is not None
    assert secrets[0]["site"] == "gitlab.com"
    assert secrets[0]["password"] == "new-password"


def test_delete_secret_removes_record():
    db = build_test_db()
    secret = save_secret(db, "github.com", "password", "alice")

    deleted = delete_secret(db, secret.id, "alice")
    secrets = get_secrets(db, "alice")

    assert deleted is True
    assert secrets == []


def test_save_secret_schedules_expiration_when_requested():
    db = build_test_db()

    with patch("app.services.secret_service.schedule_secret_expiration") as mock_schedule:
        secret = save_secret(
            db,
            "example.com",
            "password",
            "alice",
            expires_in_days=7,
        )

    assert secret is not None
    mock_schedule.assert_called_once()
