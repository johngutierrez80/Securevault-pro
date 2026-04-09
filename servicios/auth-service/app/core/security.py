from passlib.hash import bcrypt

# bcrypt tiene un límite de 72 bytes. Truncamos para evitar errores.
# En producción conviene aplicar una política de longitud o usar argon2.


def _normalize_password(password: str) -> str:
    b = password.encode("utf-8")
    if len(b) <= 72:
        return password
    truncated = b[:72]
    return truncated.decode("utf-8", errors="ignore")


def hash_password(password: str) -> str:
    return bcrypt.hash(_normalize_password(password))


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.verify(_normalize_password(password), hashed)
