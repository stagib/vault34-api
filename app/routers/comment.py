from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from typing import Optional
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.enums import ReactionType
from app.models import Comment, Post, CommentReaction
from app.schemas import CommentBase, CommentResponse, ReactionBase
from app.utils import get_current_user, get_optional_user

router = APIRouter(tags=["Post Comment"])


@router.get("/posts/{post_id}/comments", response_model=Page[CommentResponse])
def get_comments(
    post_id: int,
    user: Optional[dict] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    db_post = db.query(Post).filter(Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")

    paginated_comments = paginate(
        db_post.comments.order_by(
            desc(Comment.reaction_count), desc(Comment.date_created)
        )
    )

    if user:
        comment_ids = [comment.id for comment in paginated_comments.items]
        reactions = (
            db.query(CommentReaction)
            .filter(
                CommentReaction.comment_id.in_(comment_ids),
                CommentReaction.user_id == user.id,
            )
            .all()
        )

        reaction_map = {reaction.comment_id: reaction.type for reaction in reactions}
        for comment in paginated_comments.items:
            comment.user_reaction = ReactionType.NONE
            if reaction_map.get(comment.id):
                comment.user_reaction = reaction_map.get(comment.id)

    return paginated_comments


@router.post("/posts/{post_id}/comments", response_model=CommentResponse)
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
    return db_comment


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
    db_comment = (
        db.query(Comment)
        .filter(Comment.post_id == post_id, Comment.id == comment_id)
        .first()
    )
    if not db_comment:
        raise HTTPException(status_code=404, detail="Comment not found")

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
        return {
            "type": db_reaction.type,
            "likes": db_comment.likes,
            "dislikes": db_comment.dislikes,
        }

    comment_reaction = CommentReaction(
        user_id=user.id, comment_id=comment_id, type=reaction.type
    )
    db.add(comment_reaction)
    db.commit()
    return {
        "type": comment_reaction.type,
        "likes": db_comment.likes,
        "dislikes": db_comment.dislikes,
    }
