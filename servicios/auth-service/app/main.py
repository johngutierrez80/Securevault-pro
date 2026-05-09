from fastapi import FastAPI

from .core.config import settings
from .dependencies.database import SessionLocal, engine
from .models import password_reset_token  # noqa: F401
from .models.user import Base
from .routers.auth import router as auth_router
from .services.auth_service import bootstrap_initial_admin

Base.metadata.create_all(bind=engine)

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
