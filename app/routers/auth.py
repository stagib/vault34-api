from fastapi import APIRouter, Depends, Response, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models import User
from app.database import get_db
from app.utils import hash_password, verify_password, create_token


router = APIRouter(tags=["Auth"])


class UserCreate(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(response: Response, user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter_by(username=user.username).first()

    if not db_user:
        return {"error": "User not found"}

    if verify_password(db_user.password, user.password):
        token = create_token(db_user.id)
        response.set_cookie(key="auth_token", value=token)

    return {"detail": "Logged in"}
