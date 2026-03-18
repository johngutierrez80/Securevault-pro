import os

from cryptography.fernet import Fernet

# Usar clave fija o de entorno para persistencia
key = os.getenv("ENCRYPTION_KEY", Fernet.generate_key())
cipher = Fernet(key)


def encrypt(text: str) -> str:
    return cipher.encrypt(text.encode()).decode()


def decrypt(text: str) -> str:
    return cipher.decrypt(text.encode()).decode()
