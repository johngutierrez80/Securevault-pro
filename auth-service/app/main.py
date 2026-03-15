from fastapi import FastAPI
from .routers.auth import router as auth_router
from .models.user import Base
from .dependencies.database import engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth Service")

app.include_router(auth_router, tags=["auth"])