import jwt
from argon2 import PasswordHasher
from datetime import datetime, timezone, timedelta

from app.config import settings

ph = PasswordHasher()


def hash_password(password: str) -> str:
    return ph.hash(password)


def verify_password(hashed_password: str, plain_password: str) -> bool:
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except Exception:
        return False


def create_token(user_id):
    token = jwt.encode(
        {
            "id": user_id,
            "exp": datetime.now(timezone.utc) + timedelta(hours=12),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return token
