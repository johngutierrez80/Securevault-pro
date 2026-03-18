from pydantic import BaseModel


class SecretCreate(BaseModel):
    site: str
    password: str


class SecretUpdate(BaseModel):
    site: str
    password: str


class SecretResponse(BaseModel):
    id: int
    site: str
    password: str
