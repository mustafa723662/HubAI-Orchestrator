from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import get_jwt_expire_minutes, get_jwt_secret_key

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        # Malformed hash (e.g. DB predates a hashing scheme change) — never a match.
        return False


def create_access_token(user_id: int, username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=get_jwt_expire_minutes())
    payload = {"sub": str(user_id), "username": username, "exp": expire}
    return jwt.encode(payload, get_jwt_secret_key(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Raises jwt.PyJWTError (or a subclass) if the token is invalid/expired."""
    return jwt.decode(token, get_jwt_secret_key(), algorithms=[ALGORITHM])
