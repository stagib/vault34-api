from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models import Post, Tag
from app.database import get_db
from app.dependencies import get_current_user
from app.schemas import PostCreate, PostResponse


router = APIRouter(tags=["Post"])


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


@router.get("/posts", response_model=list[PostResponse])
def get_posts(db: Session = Depends(get_db)):
    return db.query(Post).all()


@router.post("/posts")
def create_post(
    post: PostCreate,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_post = Post(title=post.title, user_id=user.id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)

    add_tag(db, post.tags, db_post)
    return {"detail": "hello"}


@router.get("/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: int, db: Session = Depends(get_db)):
    db_post = db.query(Post).filter(Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="post not found")
    return db_post


@router.put("/posts/{post_id}", response_model=PostResponse)
def update_post(
    post_id: int,
    post: PostCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    db_post = db.query(Post).filter(Post.id == post_id, Post.user_id == user.id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="post not found")

    for k, v in post.model_dump(exclude_unset=True).items():
        if k == "tags":
            continue
        setattr(db_post, k, v)

    db.commit()
    db.refresh(db_post)
    add_tag(db, post.tags, db_post)
    return db_post


@router.delete("/posts/{post_id}")
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    db_post = db.query(Post).filter(Post.id == post_id, Post.user_id == user.id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="post not found")

    db.delete(db_post)
    db.commit()
    return {"detail": "alskdmfmksf"}
