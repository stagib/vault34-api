import jwt
from argon2 import PasswordHasher
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Post, Tag

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
