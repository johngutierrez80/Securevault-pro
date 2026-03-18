from cryptography.fernet import Fernet

key = Fernet.generate_key()
cipher = Fernet(key)


def encrypt(text: str):
    return cipher.encrypt(text.encode()).decode()


def decrypt(text: str):
    return cipher.decrypt(text.encode()).decode()
