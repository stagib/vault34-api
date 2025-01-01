import jwt
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.models import User
from app.database import get_db
from app.utils import hash_password, verify_password


router = APIRouter(tags=["Auth"])


class UserCreate(BaseModel):
    username: str
    password: str


@router.post("/register")
def register_user(response: Response, user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = hash_password(user.password)
    db_user = User(username=user.username, password=hashed_password)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    token = jwt.encode(
        {
            "id": db_user.id,
            "exp": datetime.now(timezone.utc) + timedelta(hours=12),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    response.set_cookie(key="auth_token", value=token)

    return {"token": f"{token}"}


@router.post("/login")
def login(response: Response, user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter_by(username=user.username).first()

    if not db_user:
        return {"error": "user not found"}

    if verify_password(db_user.password, user.password):
        token = jwt.encode(
            {
                "id": db_user.id,
                "exp": datetime.now(timezone.utc) + timedelta(hours=12),
            },
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )

        response.set_cookie(key="auth_token", value=token)

    return {"sdfsfsn": "sdfdsf"}
