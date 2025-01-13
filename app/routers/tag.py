from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tag
from app.schemas import TagBase

router = APIRouter(tags=["Tag"])


@router.get("/tags", response_model=list[TagBase])
def get_tags(db: Session = Depends(get_db)):
    tags = db.query(Tag).all()
    return tags
