from pydantic import BaseModel
from datetime import datetime

from app.enums import TagType, ReactionType


class UserBase(BaseModel):
    id: int
    username: str


class UserCreate(BaseModel):
    username: str
    password: str


class TagBase(BaseModel):
    name: str
    type: TagType


class PostBase(BaseModel):
    id: int


class PostCreate(BaseModel):
    title: str
    tags: list[TagBase]


class PostResponse(BaseModel):
    id: int
    title: str
    date_created: datetime
    time_since: str
    likes: int
    dislikes: int
    user_reaction: ReactionType = ReactionType.NONE
    user: UserBase
    tags: list[TagBase]


class VaultBase(BaseModel):
    title: str


class VaultResponse(BaseModel):
    id: int
    title: str
    date_created: datetime
    user: UserBase


class CommentBase(BaseModel):
    content: str


class CommentResponse(BaseModel):
    id: int
    date_created: datetime
    likes: int
    dislikes: int
    user_reaction: ReactionType = ReactionType.NONE
    content: str
    user: UserBase


class ReactionBase(BaseModel):
    type: ReactionType


class PostReactionResponse(BaseModel):
    id: int
    date_created: datetime
    type: ReactionType
    post: PostBase
    user: UserBase


class ReportCreate(BaseModel):
    detail: str
    target_id: int
    target_type: str


class ReportResponse(BaseModel):
    id: int
    date_created: datetime
    target_id: int
    target_type: str
    detail: str
    user: UserBase


class FileBase(BaseModel):
    id: int
    filename: str
    size: int
    content_type: str
