import redis
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://vault:vault@postgres:5432/vaultdb"
    secret_key: str = "securevaultsecret"
    algorithm: str = "HS256"
    auth_session_validate_url: str = "http://auth:8001/session/validate"

    mailjet_api_key: str | None = None
    mailjet_secret_key: str | None = None
    mailjet_sender_email: str = "johngutierrez80@gmail.com"
    mailjet_sender_name: str = "SecureVault Pro"

    class Config:
        env_file = ".env"


settings = Settings()

# Redis client for caching, rate limiting and async worker queues.
redis_client = redis.Redis(
    host="redis",
    port=6379,
    db=0,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2,
)
