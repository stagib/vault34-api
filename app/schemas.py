from pydantic import BaseModel
from datetime import datetime

from app.enums import TagType, ReactionType, ReportType, Privacy


class UserBase(BaseModel):
    id: int
    username: str


class UserResponse(BaseModel):
    id: int
    username: str
    time_since: str
    vault_count: int
    post_count: int
    comment_count: int
    liked_posts: int


class UserCreate(BaseModel):
    username: str
    password: str


class TagBase(BaseModel):
    name: str
    type: TagType
    count: int


class PostBase(BaseModel):
    id: int
    thumbnail: str = None


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
    privacy: Privacy


class VaultResponse(BaseModel):
    id: int
    title: str
    privacy: Privacy
    time_since: str
    user: UserBase
    post_count: int


class UserVaultResponse(BaseModel):
    id: int
    title: str
    privacy: Privacy
    time_since: str
    user: UserBase
    post_count: int
    has_post: bool = False
    posts: list[PostBase]


class CommentBase(BaseModel):
    content: str


class CommentResponse(BaseModel):
    id: int
    date_created: datetime
    time_since: str
    likes: int
    dislikes: int
    user_reaction: ReactionType = ReactionType.NONE
    content: str
    user: UserBase
    post: PostBase


class ReactionBase(BaseModel):
    type: ReactionType


class PostReactionResponse(BaseModel):
    id: int
    date_created: datetime
    type: ReactionType
    post: PostBase


class ReportCreate(BaseModel):
    detail: str
    target_id: int
    target_type: ReportType


class ReportResponse(BaseModel):
    id: int
    date_created: datetime
    target_id: int
    target_type: ReportType
    detail: str
    user: UserBase


class FileBase(BaseModel):
    id: int
    filename: str
    content_type: str
    src: str = None
