import os
from PIL import Image
from moviepy import VideoFileClip
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session
from uuid import uuid4

from app.config import settings
from app.database import get_db
from app.models import Post, PostFile
from app.schemas import FileBase
from app.utils import get_current_user


router = APIRouter(tags=["Post File"])


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


@router.get("/posts/{post_id}/files", response_model=Page[FileBase])
def get_post_files(post_id: int, db: Session = Depends(get_db)):
    db_post = db.query(Post).filter(Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")

    paginated_files = paginate(db_post.files)
    for file in paginated_files.items:
        file.src = f"{settings.API_URL}/posts/{db_post.id}/files/{file.filename}"
    return paginated_files


@router.post("/posts/{post_id}/files")
async def upload_files(
    post_id: int,
    user: dict = Depends(get_current_user),
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id, Post.user_id == user.id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    for file in files:
        if (
            file.content_type
            not in settings.ALLOWED_IMAGE_TYPES + settings.ALLOWED_VIDEO_TYPES
        ):
            raise HTTPException(status_code=400, detail="Unsupported file type")

        if file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large")

        filename = unique_filename(file)
        thumbnail_filename = create_thumbnail_filename(file, filename)
        file_path = create_file_path(filename, user.username, post_id)
        thumbnail_path = create_file_path(thumbnail_filename, user.username, post_id)

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

    return {"detail": "Files added"}


@router.get("/posts/{post_id}/files/{filename}")
def get_file(
    post_id: int, filename: str, type: str = Query(None), db: Session = Depends(get_db)
):
    file = (
        db.query(PostFile)
        .filter(PostFile.post_id == post_id, PostFile.filename == filename)
        .first()
    )
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    path = file.file_path
    if type == "thumbnail":
        path = file.thumbnail_path

    file_path = os.path.join(settings.UPLOAD_FOLDER, path)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path, media_type=file.content_type)


@router.delete("/posts/{post_id}/files/{file_id}")
def delete_file(
    post_id: int,
    file_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id, Post.user_id == user.id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    file = (
        db.query(PostFile)
        .filter(PostFile.post_id == post_id, PostFile.id == file_id)
        .first()
    )
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = os.path.join(settings.UPLOAD_FOLDER, file.file_path)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(file)
    db.commit()
    return {"detail": "Removed file"}
