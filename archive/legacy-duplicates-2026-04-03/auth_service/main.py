import os

import jwt
from fastapi import Depends, FastAPI, HTTPException
from passlib.hash import bcrypt
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

# Configuración DB (usar variables de entorno en producción)
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://vault:vault@postgres:5432/vaultdb"
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Modelo de tabla User
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)


# Crear tablas automáticamente al iniciar
Base.metadata.create_all(bind=engine)

SECRET = os.getenv("SECRET_KEY", "securevaultsecret")  # Mejorar con env
app = FastAPI()


# Dependencia para obtener sesión DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/register")
def register(username: str, password: str, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="User exists")

    hashed = bcrypt.hash(password)
    db_user = User(username=username, hashed_password=hashed)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"msg": "user created"}


@app.post("/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not bcrypt.verify(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = jwt.encode({"user": username}, SECRET, algorithm="HS256")
    return {"access_token": token}
