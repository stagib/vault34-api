import os
import uuid
from PIL import Image
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models import Post, PostFile
from app.database import get_db
from app.dependencies import get_current_user
from app.config import settings


router = APIRouter(tags=["Post File"])


class FileBase(BaseModel):
    id: int
    filename: str
    size: int
    content_type: str


@router.get("/posts/{post_id}/files", response_model=list[FileBase])
def get_post_files(post_id: int, db: Session = Depends(get_db)):
    db_post = db.query(Post).filter(Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="post not found")
    return db_post.files


@router.post("/posts/{post_id}/files")
async def upload_files(
    post_id: int,
    user: Optional[dict] = Depends(get_current_user),
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id, Post.user_id == user.id).first()
    if not post:
        raise HTTPException(status_code=404, detail="post not found")

    for file in files:
        if (
            file.content_type
            not in settings.ALLOWED_IMAGE_TYPES + settings.ALLOWED_VIDEO_TYPES
        ):
            raise HTTPException(status_code=400, detail="unsupported file type")

        _, ext = os.path.splitext(file.filename)
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        upload_path = os.path.join(settings.UPLOAD_FOLDER, user.username, str(post_id))
        file_path = os.path.join(upload_path, unique_filename)

        os.makedirs(upload_path, exist_ok=True)
        with open(file_path, "wb") as f:
            while content := await file.read(1024 * 1024):
                f.write(content)

        file_width = file_height = None
        if file.content_type in settings.ALLOWED_IMAGE_TYPES:
            with Image.open(file_path) as img:
                file_width, file_height = img.size

        post_file = PostFile(
            post_id=post.id,
            filename=unique_filename,
            content_type=file.content_type,
            file_path=os.path.relpath(file_path, settings.UPLOAD_FOLDER),
            size=file.size,
            width=file_width,
            height=file_height,
        )

        db.add(post_file)
        db.commit()
        db.refresh(post_file)

    return {"detail": "hello"}


@router.get("/posts/{post_id}/files/{file_id}")
def get_file(post_id: int, file_id: int, db: Session = Depends(get_db)):
    file = db.query(PostFile).filter(Post.id == post_id, PostFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="file not found")

    file_path = os.path.join(settings.UPLOAD_FOLDER, file.file_path)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="file not found")

    return FileResponse(file_path, media_type=file.content_type)


@router.delete("/posts/{post_id}/files/{file_id}")
def delete_file(
    post_id: int,
    file_id: int,
    user: Optional[dict] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    file = db.query(PostFile).filter(Post.id == post_id, PostFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="file not found")

    db.delete(file)
    db.commit()
    return {"salkdfkma": "sdlkmffskml"}
