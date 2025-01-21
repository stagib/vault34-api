from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session
from typing import Optional

from app.config import settings
from app.database import get_db
from app.models import Post, PostReaction, PostFile
from app.schemas import PostCreate, PostResponse, ReactionBase, PostBase
from app.utils import add_tag, get_current_user, get_optional_user


router = APIRouter(tags=["Post"])


@router.get("/posts", response_model=Page[PostBase])
def get_posts(db: Session = Depends(get_db)):
    paginated_posts = paginate(db.query(Post))
    for post in paginated_posts.items:
        post_file = db.query(PostFile).filter(PostFile.post_id == post.id).first()
        if post_file:
            post.thumbnail = (
                f"{settings.API_URL}/posts/{post.id}/files/{post_file.filename}"
            )
    return paginated_posts


@router.post("/posts", response_model=PostResponse)
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
    return db_post


@router.get("/posts/{post_id}", response_model=PostResponse)
def get_post(
    post_id: int,
    user: Optional[dict] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    db_post = db.query(Post).filter(Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")

    if user:
        reaction = db_post.reactions.filter(PostReaction.user_id == user.id).first()
        if reaction:
            db_post.user_reaction = reaction.type

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
        raise HTTPException(status_code=404, detail="Post not found")

    for key, value in post.model_dump(exclude_unset=True).items():
        if key == "tags":
            continue
        setattr(db_post, key, value)

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
        raise HTTPException(status_code=404, detail="Post not found")

    db.delete(db_post)
    db.commit()
    return {"detail": "Post removed"}


@router.post("/posts/{post_id}/reactions")
def react_to_post(
    reaction: ReactionBase,
    post_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_post = db.query(Post).filter(Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")

    db_reaction = (
        db.query(PostReaction)
        .filter(
            PostReaction.post_id == post_id,
            PostReaction.user_id == user.id,
        )
        .first()
    )
    if db_reaction:
        db_reaction.type = reaction.type
        db.commit()
        return {
            "type": db_reaction.type,
            "likes": db_post.likes,
            "dislikes": db_post.dislikes,
        }

    post_reaction = PostReaction(user_id=user.id, post_id=post_id, type=reaction.type)
    db.add(post_reaction)
    db.commit()
    return {
        "type": post_reaction.type,
        "likes": db_post.likes,
        "dislikes": db_post.dislikes,
    }
