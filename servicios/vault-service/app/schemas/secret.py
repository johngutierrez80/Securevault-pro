from pydantic import BaseModel
from pydantic import Field


class SecretCreate(BaseModel):
    site: str
    password: str
    expires_in_days: int | None = Field(default=None, ge=1, le=3650)


class SecretUpdate(BaseModel):
    site: str
    password: str
    expires_in_days: int | None = Field(default=None, ge=1, le=3650)


class SecretResponse(BaseModel):
    id: int
    site: str
    password: str
