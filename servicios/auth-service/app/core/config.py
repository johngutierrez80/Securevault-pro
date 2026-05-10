from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://vault:vault@postgres:5432/vaultdb"
    secret_key: str = "securevaultsecret"
    algorithm: str = "HS256"
    token_exp_minutes: int = 60
    admin_token_exp_minutes: int = 480  # 8 horas para administradores
    bootstrap_admin_email: str | None = None
    bootstrap_admin_password: str | None = None

    # Email configuration
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str = "noreply@securevault.local"
    email_verification_minutes: int = 30
    require_email_verification: bool = True

    # Mailjet API
    mailjet_api_key: str | None = None
    mailjet_secret_key: str | None = None
    mailjet_sender_email: str = "johngutierrez80@gmail.com"
    mailjet_sender_name: str = "SecureVault Pro"

    class Config:
        env_file = ".env"


settings = Settings()

# Cliente Redis para tracking de intentos fallidos de login
try:
    import redis as _redis
    redis_client = _redis.Redis(
        host="redis",
        port=6379,
        db=1,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )
except Exception:
    redis_client = None
