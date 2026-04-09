from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from crypto import encrypt, decrypt
import os

# Configuración DB
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://vault:vault@postgres:5432/vaultdb")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelo de tabla Secret
class Secret(Base):
    __tablename__ = "secrets"
    id = Column(Integer, primary_key=True, index=True)
    site = Column(String)
    encrypted_password = Column(String)
    owner = Column(String, index=True)  # Usuario propietario

# Crear tablas automáticamente
Base.metadata.create_all(bind=engine)

# Modelo Pydantic para requests
class SecretRequest(BaseModel):
    site: str
    password: str

SECRET_KEY = os.getenv("SECRET_KEY", "securevaultsecret")
ALGORITHM = "HS256"
security = HTTPBearer()
app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("user")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
        return username
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado")

@app.post("/secret")
def save(request: SecretRequest, username: str = Depends(verify_token), db: Session = Depends(get_db)):
    try:
        enc = encrypt(request.password)
        db_secret = Secret(site=request.site, encrypted_password=enc, owner=username)
        db.add(db_secret)
        db.commit()
        db.refresh(db_secret)
        return {"msg": "saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar: {str(e)}")

@app.get("/secret")
def get_all(username: str = Depends(verify_token), db: Session = Depends(get_db)):
    try:
        secrets = db.query(Secret).filter(Secret.owner == username).all()
        result = []
        for s in secrets:
            result.append({
                "site": s.site,
                "password": decrypt(s.encrypted_password)
            })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al recuperar: {str(e)}")