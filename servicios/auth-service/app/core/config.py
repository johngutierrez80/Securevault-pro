from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://vault:vault@postgres:5432/vaultdb"
    secret_key: str = "securevaultsecret"
    algorithm: str = "HS256"
    token_exp_minutes: int = 60
    bootstrap_admin_email: str | None = None
    bootstrap_admin_password: str | None = None

    class Config:
        env_file = ".env"


settings = Settings()
