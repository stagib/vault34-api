import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from uuid import uuid4

from app.config import settings
from app.database import get_db
from app.models import User
from app.schemas import UserBase, VaultResponse, PostBase, CommentResponse
from app.dependencies import get_current_user

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


@router.get("/users/{username}/profile-picture")
def get_user_profile_picture(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    file_path = os.path.join(settings.UPLOAD_FOLDER, user.profile_picture)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="file not found")
    return FileResponse(file_path)


@router.post("/users/{username}/profile-picture")
async def upload_user_profile_picture(
    username: str,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.username != username:
        raise HTTPException(status_code=401, detail="Not authorized")

    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    _, ext = os.path.splitext(file.filename)
    unique_filename = f"{uuid4().hex}{ext}"
    upload_path = os.path.join(settings.UPLOAD_FOLDER, user.username, "profilepicture")
    file_path = os.path.join(upload_path, unique_filename)

    os.makedirs(upload_path, exist_ok=True)
    with open(file_path, "wb") as f:
        while content := await file.read(1024 * 1024):
            f.write(content)

    user.profile_picture = os.path.relpath(file_path, settings.UPLOAD_FOLDER)
    db.commit()
    return {"detail": "Updated user profile picture"}
