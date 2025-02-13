import jwt
import os
from argon2 import PasswordHasher
from PIL import Image
from moviepy import VideoFileClip
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, Depends, Cookie, UploadFile
from typing import Annotated
from sqlalchemy.orm import Session
from uuid import uuid4

from app.config import settings
from app.database import get_db
from app.models import Post, Tag, User, PostFile

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

        user = db.query(User).filter(User.id == user_id).first()
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

        user = db.query(User).filter(User.id == user_id).first()
        if not user or user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.InvalidTokenError:
        return None


"""
File functions
"""


def get_image_size(file, file_path):
    if file.content_type in settings.ALLOWED_IMAGE_TYPES:
        with Image.open(file_path) as img:
            return img.size
    return (None, None)


def unique_filename(file):
    _, ext = os.path.splitext(file.filename)
    unique_filename = f"{uuid4().hex}{ext}"
    return unique_filename


def create_thumbnail_filename(file, filename):
    name, ext = os.path.splitext(filename)
    if file.content_type in settings.ALLOWED_IMAGE_TYPES:
        return f"thumb_{name}{ext}"
    if file.content_type in settings.ALLOWED_VIDEO_TYPES:
        return f"thumb_{name}.jpg"


def create_file_path(filename, username, post_id):
    upload_path = os.path.join(settings.UPLOAD_FOLDER, username, "posts", str(post_id))
    file_path = os.path.join(upload_path, filename)
    os.makedirs(upload_path, exist_ok=True)
    return file_path


def create_image_thumbnail(file_path, thumbnail_path):
    with Image.open(file_path) as img:
        img.thumbnail(size=(1024, 1024))
        img.save(thumbnail_path)


def create_video_thumbnail(file_path, thumbnail_path):
    clip = VideoFileClip(file_path)
    frame = clip.get_frame(1)
    image = Image.fromarray(frame)
    image.thumbnail(size=(1024, 1024))
    image.save(thumbnail_path)


def create_thumbnail(file, file_path, thumbnail_path):
    if file.content_type in settings.ALLOWED_IMAGE_TYPES:
        create_image_thumbnail(file_path, thumbnail_path)
    elif file.content_type in settings.ALLOWED_VIDEO_TYPES:
        create_video_thumbnail(file_path, thumbnail_path)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")


async def download_file(file, file_path):
    with open(file_path, "wb") as f:
        while content := await file.read(1024 * 1024):
            f.write(content)


def validate_files(files: list[UploadFile]):
    for file in files:
        if (
            file.content_type
            not in settings.ALLOWED_IMAGE_TYPES + settings.ALLOWED_VIDEO_TYPES
        ):
            raise HTTPException(status_code=400, detail="Unsupported file type")
        if file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large")
    return True


async def add_files(db: Session, files: list[UploadFile], post: Post, user: dict):
    for file in files:
        filename = unique_filename(file)
        thumbnail_filename = create_thumbnail_filename(file, filename)
        file_path = create_file_path(filename, user.username, post.id)
        thumbnail_path = create_file_path(thumbnail_filename, user.username, post.id)

        await download_file(file, file_path)
        create_thumbnail(file, file_path, thumbnail_path)
        file_width, file_height = get_image_size(file, file_path)

        post_file = PostFile(
            post_id=post.id,
            filename=filename,
            content_type=file.content_type,
            file_path=os.path.relpath(file_path, settings.UPLOAD_FOLDER),
            thumbnail_path=os.path.relpath(thumbnail_path, settings.UPLOAD_FOLDER),
            size=file.size,
            width=file_width,
            height=file_height,
        )

        db.add(post_file)
        db.commit()
        db.refresh(post_file)
