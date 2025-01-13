from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.dependencies import get_optional_user
from app.models import Report, Comment, User, Post
from app.schemas import ReportCreate, ReportResponse

router = APIRouter(tags=["Report"])


@router.post("/reports", response_model=ReportResponse)
def create_report(
    report: ReportCreate,
    user: Optional[dict] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    if report.target_type == "user":
        db_user = db.query(User).filter(User.id == report.target_id).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
    elif report.target_type == "post":
        db_post = db.query(Post).filter(Post.id == report.target_id).first()
        if not db_post:
            raise HTTPException(status_code=404, detail="Post not found")
    elif report.target_type == "comment":
        db_comment = db.query(Comment).filter(Comment.id == report.target_id).first()
        if not db_comment:
            raise HTTPException(status_code=404, detail="Comment not found")

    db_report = Report(
        user_id=user.id,
        target_id=report.target_id,
        target_type=report.target_type,
        detail=report.detail,
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report
