import jwt
from fastapi import Request, HTTPException, Cookie, Depends
from typing import Optional, Annotated
from sqlalchemy.orm import Session

from app.config import settings
from app.models import User
from app.database import get_db


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
            raise HTTPException(status_code=401, detail="user not found")
        return user

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_optional_user(request: Request) -> Optional[dict]:
    token = request.cookies.get("authToken")

    if not token:
        return None

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        id = payload.get("id")
        if not id:
            return None
        return {"username": id}
    except jwt.InvalidTokenError:
        return None
