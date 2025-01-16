from pydantic import BaseModel
from datetime import datetime
from typing import Literal, Optional


class UserBase(BaseModel):
    id: int
    username: str


class TagBase(BaseModel):
    name: str
    type: Literal["Artist", "General", "Character", "Series"]


class PostBase(BaseModel):
    id: int


class PostCreate(BaseModel):
    title: str
    tags: list[TagBase]


class PostResponse(BaseModel):
    id: int
    title: str
    date_created: datetime
    likes: int
    dislikes: int
    user_reaction: Optional[str] = None
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
    user_reaction: Optional[str] = None
    content: str
    user: UserBase


class ReactionBase(BaseModel):
    type: str


class PostReactionResponse(BaseModel):
    id: int
    date_created: datetime
    type: str
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
