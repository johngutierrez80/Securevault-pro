from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from .user import Base


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True, nullable=False)
    token_hash = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    confirmed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    # Almacena la contraseña hasheada del registro pendiente.
    # NULL significa que el usuario ya existe en la tabla users (flujo antiguo).
    hashed_password = Column(String, nullable=True)
