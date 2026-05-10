from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..core.rate_limit import limiter
from ..core.security import verify_token_context
from ..dependencies.database import get_db
from ..schemas.secret import SecretAdminResponse, SecretCreate, SecretResponse, SecretUpdate, ShareSecretRequest
from ..services.secret_service import (
    delete_secret_admin,
    get_all_secrets,
    delete_secret,
    get_secret_by_id,
    get_secrets,
    save_secret,
    update_secret_admin,
    update_secret,
)
from ..utils.email_service import send_secret_email

router = APIRouter()


@router.post("/secret", response_model=dict)
@limiter.limit("10/minute")
def save(
    payload: SecretCreate,
    request: Request,
    token_context: dict = Depends(verify_token_context),
    db: Session = Depends(get_db),
):
    username = token_context["user"]
    try:
        save_secret(
            db,
            payload.site,
            payload.password,
            username,
            payload.category,
            payload.description,
            payload.expires_in_days,
        )
        return {"msg": "saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}") from e


@router.put("/secret/{secret_id}", response_model=dict)
@limiter.limit("10/minute")
def edit_secret(
    secret_id: int,
    payload: SecretUpdate,
    request: Request,
    token_context: dict = Depends(verify_token_context),
    db: Session = Depends(get_db),
):
    username = token_context["user"]
    role = token_context["role"]
    if role == "admin":
        secret = update_secret_admin(
            db,
            secret_id,
            username,
            payload.site,
            payload.password,
            payload.category,
            payload.description,
            payload.expires_in_days,
        )
    else:
        secret = update_secret(
            db,
            secret_id,
            username,
            payload.site,
            payload.password,
            payload.category,
            payload.description,
            payload.expires_in_days,
        )
    if not secret:
        raise HTTPException(status_code=404, detail="Secret not found")
    return {"msg": "updated"}


@router.delete("/secret/{secret_id}", response_model=dict)
@limiter.limit("10/minute")
def remove_secret(
    secret_id: int,
    request: Request,
    token_context: dict = Depends(verify_token_context),
    db: Session = Depends(get_db),
):
    username = token_context["user"]
    role = token_context["role"]
    deleted = (
        delete_secret_admin(db, secret_id, username)
        if role == "admin"
        else delete_secret(db, secret_id, username)
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Secret not found")
    return {"msg": "deleted"}


@router.get("/secret", response_model=list[SecretResponse | SecretAdminResponse])
@limiter.limit("10/minute")
def get_all(
    request: Request,
    token_context: dict = Depends(verify_token_context),
    db: Session = Depends(get_db),
):
    try:
        username = token_context["user"]
        role = token_context["role"]
        if role == "admin":
            return get_all_secrets(db)
        return get_secrets(db, username)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}") from e


@router.post("/secret/{secret_id}/share", response_model=dict)
@limiter.limit("5/minute")
async def share_secret(
    secret_id: int,
    payload: ShareSecretRequest,
    request: Request,
    token_context: dict = Depends(verify_token_context),
    db: Session = Depends(get_db),
):
    username = token_context["user"]
    role = token_context["role"]

    secret = get_secret_by_id(db, secret_id)
    if not secret:
        raise HTTPException(status_code=404, detail="Secreto no encontrado")
    if secret.owner != username and role != "admin":
        raise HTTPException(status_code=403, detail="No tienes permiso para compartir este secreto")

    from ..utils.crypto import decrypt
    try:
        secret_value = decrypt(secret.encrypted_password)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al descifrar el secreto: {str(e)}") from e

    sent = await send_secret_email(payload.to_email, secret.site, secret_value, username)
    if not sent:
        raise HTTPException(status_code=502, detail="No se pudo enviar el correo. Verifica la dirección e intenta de nuevo.")

    return {"msg": f"Secreto '{secret.site}' enviado a {payload.to_email}"}
