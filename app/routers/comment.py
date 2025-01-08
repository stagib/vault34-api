from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Comment, Post, CommentReaction
from app.dependencies import get_current_user
from app.schemas import CommentBase, CommentResponse, ReactionBase

router = APIRouter(tags=["Post Comment"])


@router.get("/posts/{post_id}/comments", response_model=list[CommentResponse])
def get_comments(
    post_id: int,
    db: Session = Depends(get_db),
):
    db_post = db.query(Post).filter(Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")
    return db_post.comments


@router.post("/posts/{post_id}/comments")
def create_comment(
    post_id: int,
    comment: CommentBase,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_post = db.query(Post).filter(Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")

    db_comment = Comment(user_id=user.id, post_id=db_post.id, content=comment.content)
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return {"detail": "Comment created"}


@router.delete("/posts/{post_id}/comments/{comment_id}")
def delete_comment(
    post_id: int,
    comment_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_comment = (
        db.query(Comment)
        .filter(
            Comment.id == comment_id,
            Comment.post_id == post_id,
            Comment.user_id == user.id,
        )
        .first()
    )
    if not db_comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    db.delete(db_comment)
    db.commit()
    return {"detail": "Removed comment"}


@router.post("/posts/{post_id}/comments/{comment_id}/reactions")
def react_to_comment(
    post_id: int,
    comment_id: int,
    reaction: ReactionBase,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_post = db.query(Post).filter(Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")

    db_reaction = (
        db.query(CommentReaction)
        .filter(
            CommentReaction.comment_id == comment_id,
            CommentReaction.user_id == user.id,
        )
        .first()
    )

    if db_reaction:
        db_reaction.type = reaction.type
        db.commit()
        return {"detail": "Reaction updated"}

    comment_reaction = CommentReaction(
        user_id=user.id, comment_id=comment_id, type=reaction.type
    )
    db.add(comment_reaction)
    db.commit()
    return {"detail": "Reaction added"}
