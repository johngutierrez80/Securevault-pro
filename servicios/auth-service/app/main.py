from fastapi import FastAPI
from sqlalchemy import inspect, text

from .core.config import settings
from .dependencies.database import SessionLocal, engine
from .models import admin_audit_log  # noqa: F401
from .models import auth_session  # noqa: F401
from .models import password_reset_token  # noqa: F401
from .models.user import Base
from .routers.auth import router as auth_router
from .services.auth_service import bootstrap_initial_admin


def ensure_schema_compatibility() -> None:
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    user_columns = {column["name"] for column in inspector.get_columns("users")}
    if "is_active" in user_columns:
        return

    with engine.begin() as connection:
        # Backward-compatible migration for environments created before is_active existed.
        connection.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE"))


Base.metadata.create_all(bind=engine)
ensure_schema_compatibility()

app = FastAPI(title="Auth Service")

app.include_router(auth_router, tags=["auth"])


@app.on_event("startup")
def create_bootstrap_admin_if_needed():
    db = SessionLocal()
    try:
        bootstrap_initial_admin(
            db,
            settings.bootstrap_admin_email,
            settings.bootstrap_admin_password,
        )
    finally:
        db.close()
