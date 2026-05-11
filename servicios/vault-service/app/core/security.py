import jwt
import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError

from ..core.config import settings

security = HTTPBearer()


def _validate_session_with_auth_service(token: str) -> dict:
    try:
        response = httpx.get(
            settings.auth_session_validate_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=2,
        )
        if response.status_code in {401, 403}:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Sesión inválida o revocada",
            )
        response.raise_for_status()
        payload = response.json()
        if not payload.get("is_active", False):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario desactivado",
            )
        return payload
    except HTTPException:
        raise
    except httpx.HTTPStatusError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo validar la sesión",
        ) from error
    except httpx.RequestError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo validar la sesión",
        ) from error


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        username: str = payload.get("user")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido"
            )

        _ = _validate_session_with_auth_service(token)
        return username
    except InvalidTokenError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado"
        ) from err


def verify_token_context(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        username: str = payload.get("user")
        remote_session = _validate_session_with_auth_service(token)
        role: str = remote_session.get("role", payload.get("role", "user"))
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido"
            )
        if role not in {"admin", "user"}:
            role = "user"
        return {"user": username, "role": role}
    except InvalidTokenError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado"
        ) from err
