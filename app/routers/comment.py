from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Comment, Post
from app.dependencies import get_current_user
from app.schemas import CommentBase

router = APIRouter(tags=["Post Comment"])


@router.post("/posts/{post_id}/comments")
def create_comment(
    post_id: int,
    comment: CommentBase,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_post = db.query(Post).filter(Post.id == post_id, Post.user_id == user.id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")

    db_comment = Comment(user_id=user.id, post_id=db_post.id, content=comment.content)
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return {"detail": "Comment created"}
