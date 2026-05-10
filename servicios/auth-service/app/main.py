from fastapi import FastAPI
from sqlalchemy import inspect, text

from .core.config import settings
from .dependencies.database import SessionLocal, engine
from .models import admin_audit_log  # noqa: F401
from .models import auth_session  # noqa: F401
from .models import email_verification_token  # noqa: F401
from .models import password_reset_token  # noqa: F401
from .models.user import Base
from .routers.auth import router as auth_router
from .services.auth_service import bootstrap_initial_admin


def ensure_schema_compatibility() -> None:
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    user_columns = {column["name"] for column in inspector.get_columns("users")}
    if "is_active" not in user_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE"))

    if "email_verified" not in user_columns:
        with engine.begin() as connection:
            # Admin bootstrap se marca como verificado automáticamente
            connection.execute(text("ALTER TABLE users ADD COLUMN email_verified BOOLEAN NOT NULL DEFAULT FALSE"))
            connection.execute(text("UPDATE users SET email_verified = TRUE WHERE role = 'admin'"))

    # Columna para registros pendientes de verificación (nuevo flujo)
    if "email_verification_tokens" in inspector.get_table_names():
        evt_columns = {column["name"] for column in inspector.get_columns("email_verification_tokens")}
        if "hashed_password" not in evt_columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE email_verification_tokens ADD COLUMN hashed_password VARCHAR"))


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
