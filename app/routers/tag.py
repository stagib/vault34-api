from fastapi import APIRouter, Depends, Query
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tag
from app.schemas import TagBase

router = APIRouter(tags=["Tag"])


@router.get("/tags", response_model=Page[TagBase])
def get_tags(
    query: str = Query(None, min_length=1),
    db: Session = Depends(get_db),
):
    if not query:
        tags = db.query(Tag)
        return paginate(tags)

    tags = db.query(Tag).filter(Tag.name.ilike(f"%{query}%"))
    return paginate(tags)
