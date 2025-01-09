from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserBase, VaultResponse, PostBase, CommentResponse

router = APIRouter(tags=["User"])


@router.get("/users/{username}", response_model=UserBase)
def get_user(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/users/{username}/posts", response_model=list[PostBase])
def get_user_posts(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.posts


@router.get("/users/{username}/posts/reactions")
def get_user_post_reactions(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.post_reactions


@router.get("/users/{username}/comments", response_model=list[CommentResponse])
def get_user_comments(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.comments


@router.get("/users/{username}/vaults", response_model=list[VaultResponse])
def get_user_vaults(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    vaults = []
    for vault in user.vaults:
        vaults.append(
            {
                "id": vault.id,
                "title": vault.title,
                "date_created": vault.date_created,
                "posts": vault.posts[-3:],
            }
        )
    return vaults
