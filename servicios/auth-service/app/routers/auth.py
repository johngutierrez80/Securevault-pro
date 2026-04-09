from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..dependencies.database import get_db
from ..schemas.user import Token, UserCreate, UserLogin
from ..services.auth_service import authenticate_user, register_user

router = APIRouter()


@router.post("/register", response_model=dict)
def register(user: UserCreate, db: Session = Depends(get_db)):
    if not register_user(db, user.username, user.password):
        raise HTTPException(status_code=400, detail="User already exists")
    return {"msg": "User created"}


@router.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    token = authenticate_user(db, user.username, user.password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": token}
