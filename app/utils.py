import jwt
from argon2 import PasswordHasher
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, Depends, Cookie
from typing import Annotated
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Post, Tag, User

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


def add_tag(db: Session, tags: list, db_post: Post):
    db_post.tags = []
    for tag in tags:
        db_tag = (
            db.query(Tag).filter(Tag.name == tag.name, Tag.type == tag.type).first()
        )
        if not db_tag:
            db_tag = Tag(name=tag.name, type=tag.type)
        db_post.tags.append(db_tag)
    db.commit()


def get_current_user(
    auth_token: Annotated[str | None, Cookie()] = None,
    db: Session = Depends(get_db),
):
    if not auth_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(
            auth_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id = payload.get("id")
        if not user_id or user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = db.query(User).filter(user_id == user_id).first()
        if not user or user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_optional_user(
    auth_token: Annotated[str | None, Cookie()] = None,
    db: Session = Depends(get_db),
):
    if not auth_token:
        return None

    try:
        payload = jwt.decode(
            auth_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id = payload.get("id")
        if not user_id or user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = db.query(User).filter(user_id == user_id).first()
        if not user or user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.InvalidTokenError:
        return None
