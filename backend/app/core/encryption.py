from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_encryption_key


def encrypt_value(plaintext: str) -> str:
    """Encrypt a secret (e.g. a user's own OpenAI/Claude API key) for
    storage. Never store the plaintext value anywhere."""
    fernet = Fernet(get_encryption_key())
    return fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_value(ciphertext: str) -> str | None:
    """Decrypt a value previously produced by encrypt_value(). Returns None
    (rather than raising) if the ciphertext is invalid/tampered/was
    encrypted under a different key — callers should treat that the same
    as "no key configured", not crash the request."""
    fernet = Fernet(get_encryption_key())
    try:
        return fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError):
        return None


def mask_key(plaintext: str) -> str:
    """A short, safe-to-display preview like 'sk-ab12...cd34' — enough for
    the user to recognize which key is saved without exposing it."""
    if len(plaintext) <= 10:
        return "•" * len(plaintext)
    return f"{plaintext[:6]}...{plaintext[-4:]}"
