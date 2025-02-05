import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response, Query
from fastapi.responses import FileResponse
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session
from uuid import uuid4

from app.enums import ReactionType
import app.schemas as schemas
from app.config import settings
from app.database import get_db
from app.models import User, PostFile, PostReaction
from app.utils import hash_password, create_token, get_current_user


router = APIRouter(tags=["User"])


@router.post("/users")
def register_user(
    response: Response, user: schemas.UserCreate, db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username is already taken")

    hashed_password = hash_password(user.password)
    db_user = User(username=user.username, password=hashed_password, profile_picture="")

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    token = create_token(db_user.id)
    response.set_cookie(key="auth_token", value=token)
    return {"detail": "User registered"}


@router.get("/users/{username}", response_model=schemas.UserResponse)
def get_user(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/users/{username}/posts", response_model=Page[schemas.PostBase])
def get_user_posts(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    paginated_posts = paginate(user.posts)
    for post in paginated_posts.items:
        post_file = db.query(PostFile).filter(PostFile.post_id == post.id).first()
        if post_file:
            post.thumbnail = (
                f"{settings.API_URL}/posts/{post.id}/files/{post_file.filename}"
            )
    return paginated_posts


@router.get(
    "/users/{username}/posts/reactions",
    response_model=Page[schemas.PostBase],
)
def get_user_post_reactions(
    username: str, type: ReactionType = Query(None), db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    post_reactions = user.post_reactions
    if type:
        post_reactions = post_reactions.filter(PostReaction.type == type)

    paginated_posts = paginate(post_reactions)
    for post in paginated_posts.items:
        post_file = db.query(PostFile).filter(PostFile.post_id == post.id).first()
        if post_file:
            post.thumbnail = (
                f"{settings.API_URL}/posts/{post.id}/files/{post_file.filename}"
            )

    return paginated_posts


@router.get("/users/{username}/comments", response_model=Page[schemas.CommentResponse])
def get_user_comments(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return paginate(user.comments)


@router.get("/users/{username}/vaults", response_model=Page[schemas.UserVaultResponse])
def get_user_vaults(
    username: str, post_id: int = Query(None), db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    paginated_vaults = paginate(user.vaults)

    for vault in paginated_vaults.items:
        has_post = any(post_id == post.id for post in vault.posts)

        vault.has_post = has_post
        vault.posts = vault.posts[-3:]

        for post in vault.posts:
            post_file = db.query(PostFile).filter(PostFile.post_id == post.id).first()
            if post_file:
                post.thumbnail = (
                    f"{settings.API_URL}/posts/{post.id}/files/{post_file.filename}"
                )

    return paginated_vaults


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
