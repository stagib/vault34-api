from fastapi import APIRouter, Depends, Query
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from app.database import get_db
from app.enums import TagType
from app.models import Tag
from app.schemas import TagBase

router = APIRouter(tags=["Tag"])


@router.get("/tags", response_model=Page[TagBase])
def get_tags(
    query: str = Query(None, min_length=1),
    type: TagType = Query(None),
    db: Session = Depends(get_db),
):
    tags = db.query(Tag)

    if query:
        tags = tags.filter(Tag.name.ilike(f"%{query}%"))

    if type:
        tags = tags.filter(Tag.type == type)

    return paginate(tags)
