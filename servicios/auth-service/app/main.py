from fastapi import FastAPI

from .dependencies.database import engine
from .models.user import Base
from .routers.auth import router as auth_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth Service")

app.include_router(auth_router, tags=["auth"])
