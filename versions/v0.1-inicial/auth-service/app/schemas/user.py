from pydantic import BaseModel, StringConstraints
from typing import Annotated


UsernameStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
PasswordStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=72)]

class UserCreate(BaseModel):
    username: UsernameStr
    password: PasswordStr

class UserLogin(BaseModel):
    username: UsernameStr
    password: PasswordStr

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"