from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from .routers.secrets import router as secrets_router
from .models.secret import Base
from .dependencies.database import engine
from .core.rate_limit import limiter

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Vault Service")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# The gateway (nginx) already routes /vault/* to this service, so the router should expose
# endpoints directly at their intended paths (e.g., /secret).
app.include_router(secrets_router, tags=["vault"])