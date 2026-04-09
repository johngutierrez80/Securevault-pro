from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from ..schemas.secret import SecretCreate, SecretUpdate, SecretResponse
from ..dependencies.database import get_db
from ..core.security import verify_token
from ..core.rate_limit import limiter
from ..services.secret_service import save_secret, get_secrets, update_secret, delete_secret

router = APIRouter()

@router.post("/secret", response_model=dict)
@limiter.limit("10/minute")
def save(payload: SecretCreate, request: Request, username: str = Depends(verify_token), db: Session = Depends(get_db)):
    try:
        save_secret(db, payload.site, payload.password, username)
        return {"msg": "saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.put("/secret/{secret_id}", response_model=dict)
@limiter.limit("10/minute")
def edit_secret(
    secret_id: int,
    payload: SecretUpdate,
    request: Request,
    username: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    secret = update_secret(db, secret_id, username, payload.site, payload.password)
    if not secret:
        raise HTTPException(status_code=404, detail="Secret not found")
    return {"msg": "updated"}

@router.delete("/secret/{secret_id}", response_model=dict)
@limiter.limit("10/minute")
def remove_secret(secret_id: int, request: Request, username: str = Depends(verify_token), db: Session = Depends(get_db)):
    if not delete_secret(db, secret_id, username):
        raise HTTPException(status_code=404, detail="Secret not found")
    return {"msg": "deleted"}

@router.get("/secret", response_model=list[SecretResponse])
@limiter.limit("10/minute")
def get_all(request: Request, username: str = Depends(verify_token), db: Session = Depends(get_db)):
    try:
        return get_secrets(db, username)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")