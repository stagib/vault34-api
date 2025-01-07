from pydantic import BaseModel
from datetime import datetime
from typing import Literal


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
    user: UserBase
    tags: list[TagBase]


class VaultBase(BaseModel):
    title: str


class VaultResponse(BaseModel):
    id: int
    title: str
    date_created: datetime
    posts: list[PostBase]


class CommentBase(BaseModel):
    content: str


class CommentResponse(BaseModel):
    id: int
    user: UserBase
    date_created: datetime
    content: str
