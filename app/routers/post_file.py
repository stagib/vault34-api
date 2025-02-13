import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session


from app.config import settings
from app.database import get_db
from app.models import Post, PostFile
from app.schemas import FileBase
from app.utils import get_current_user, validate_files, add_files


router = APIRouter(tags=["Post File"])


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

    validate_files(files)
    await add_files(db, files, post, user)
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
