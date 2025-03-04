from datetime import datetime
from humanize import naturaltime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Table,
    Enum,
    select,
    func,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from app.database import Base
from app.enums import TagType, ReactionType, ReportType, Privacy


post_tag = Table(
    "post_tag",
    Base.metadata,
    Column("post_id", Integer, ForeignKey("posts.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)


post_vault = Table(
    "post_vault",
    Base.metadata,
    Column("post_id", Integer, ForeignKey("posts.id"), primary_key=True),
    Column("vault_id", Integer, ForeignKey("vaults.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    date_created = Column(DateTime, default=func.now(), nullable=True)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    profile_picture = Column(String, nullable=False)
    posts = relationship("Post", back_populates="user", lazy="dynamic")
    vaults = relationship("Vault", back_populates="user", lazy="dynamic")
    comments = relationship("Comment", back_populates="user", lazy="dynamic")
    post_reactions = relationship("PostReaction", back_populates="user", lazy="dynamic")
    comment_reactions = relationship("CommentReaction", back_populates="user")
    reports = relationship("Report", back_populates="user")

    @property
    def time_since(self) -> str:
        return naturaltime(datetime.now() - self.date_created)

    @property
    def vault_count(self) -> int:
        return self.vaults.count()

    @property
    def post_count(self) -> int:
        return self.posts.count()

    @property
    def comment_count(self) -> int:
        return self.comments.count()

    @property
    def liked_posts(self) -> int:
        return self.post_reactions.filter(PostReaction.type == "like").count()


class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date_created = Column(DateTime, default=func.now())
    title = Column(String)
    user = relationship("User", back_populates="posts")
    tags = relationship("Tag", secondary=post_tag, back_populates="posts")
    vaults = relationship("Vault", secondary=post_vault, back_populates="posts")
    files = relationship(
        "PostFile", back_populates="post", lazy="dynamic", cascade="all, delete-orphan"
    )
    comments = relationship(
        "Comment", back_populates="post", lazy="dynamic", cascade="all, delete-orphan"
    )
    reactions = relationship(
        "PostReaction",
        back_populates="post",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    @hybrid_property
    def reaction_count(self):
        return self.reactions.count()

    @reaction_count.expression
    def reaction_count(cls):
        return (
            (select(func.count(PostReaction.id)))
            .where(PostReaction.post_id == cls.id)
            .correlate(cls)
            .as_scalar()
        )

    @property
    def likes(self) -> int:
        return self.reactions.filter(PostReaction.type == "like").count()

    @property
    def dislikes(self) -> int:
        return self.reactions.filter(PostReaction.type == "dislike").count()

    @property
    def time_since(self) -> str:
        return naturaltime(datetime.now() - self.date_created)


class PostFile(Base):
    __tablename__ = "post_files"
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    date_created = Column(DateTime, default=func.now(), nullable=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    thumbnail_path = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    size = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)
    post = relationship("Post", back_populates="files")


class PostReaction(Base):
    __tablename__ = "post_reactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    date_created = Column(DateTime, default=func.now())
    type = Column(Enum(ReactionType), nullable=False, default=ReactionType.NONE)
    user = relationship("User", back_populates="post_reactions")
    post = relationship("Post", back_populates="reactions")


class Vault(Base):
    __tablename__ = "vaults"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date_created = Column(DateTime, default=func.now())
    title = Column(String, nullable=False)
    privacy = Column(Enum(Privacy), nullable=False, default=Privacy.PRIVATE)
    user = relationship("User", back_populates="vaults")
    posts = relationship(
        "Post", secondary=post_vault, back_populates="vaults", lazy="dynamic"
    )

    @property
    def post_count(self):
        return self.posts.count()

    @property
    def time_since(self) -> str:
        return naturaltime(datetime.now() - self.date_created)


class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, index=True)
    date_created = Column(DateTime, default=func.now())
    name = Column(String, nullable=False)
    type = Column(Enum(TagType), nullable=False)
    posts = relationship("Post", secondary=post_tag, back_populates="tags")

    @property
    def count(self) -> int:
        return len(self.posts)


class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    date_created = Column(DateTime, default=func.now())
    content = Column(String, nullable=False)
    user = relationship("User", back_populates="comments")
    post = relationship("Post", back_populates="comments")
    reactions = relationship(
        "CommentReaction",
        back_populates="Comment",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    @hybrid_property
    def reaction_count(self):
        return self.reactions.count()

    @reaction_count.expression
    def reaction_count(cls):
        return (
            (select(func.count(CommentReaction.id)))
            .where(CommentReaction.comment_id == cls.id)
            .correlate(cls)
            .as_scalar()
        )

    @property
    def likes(self):
        return self.reactions.filter(CommentReaction.type == "like").count()

    @property
    def dislikes(self):
        return self.reactions.filter(CommentReaction.type == "dislike").count()

    @property
    def time_since(self) -> str:
        return naturaltime(datetime.now() - self.date_created)


class CommentReaction(Base):
    __tablename__ = "comment_reactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    comment_id = Column(Integer, ForeignKey("comments.id"), nullable=False)
    date_created = Column(DateTime, default=func.now())
    type = Column(Enum(ReactionType), nullable=False, default=ReactionType.NONE)
    user = relationship("User", back_populates="comment_reactions")
    Comment = relationship("Comment", back_populates="reactions")


class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date_created = Column(DateTime, default=func.now())
    target_type = Column(Enum(ReportType), nullable=False)
    target_id = Column(Integer, nullable=False)
    detail = Column(String, nullable=False)
    user = relationship("User", back_populates="reports")
