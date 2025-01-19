from fastapi import APIRouter, Depends, Response, HTTPException
from sqlalchemy.orm import Session

from app.models import User
from app.database import get_db
from app.utils import verify_password, create_token, get_current_user
from app.schemas import UserCreate, UserBase


router = APIRouter(tags=["Auth"])


@router.get("/verify-token", response_model=UserBase)
def verify_auth_token(user: dict = Depends(get_current_user)):
    return user


@router.post("/login")
def login(response: Response, user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter_by(username=user.username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(db_user.password, user.password):
        raise HTTPException(status_code=401, detail="Username or password is incorrect")

    token = create_token(db_user.id)
    response.set_cookie(key="auth_token", value=token)
    return {"detail": "Logged in"}
