from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserBase, VaultResponse

router = APIRouter(tags=["User"])


@router.get("/users/{username}", response_model=UserBase)
def get_user(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return user


@router.get("/users/{username}/vaults", response_model=list[VaultResponse])
def get_user_vaults(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return user.vaults
