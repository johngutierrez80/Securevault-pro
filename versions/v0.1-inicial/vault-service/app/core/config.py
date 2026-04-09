from pydantic_settings import BaseSettings
import redis

class Settings(BaseSettings):
    database_url: str = "postgresql://vault:vault@postgres:5432/vaultdb"
    secret_key: str = "securevaultsecret"
    algorithm: str = "HS256"

    class Config:
        env_file = ".env"

settings = Settings()

# Redis client for caching or rate limiting
redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)