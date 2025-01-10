from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, func
from sqlalchemy.orm import relationship, backref

from app.database import Base


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
    posts = relationship("Post", back_populates="user")
    vaults = relationship("Vault", back_populates="user")
    comments = relationship("Comment", back_populates="user")
    post_reactions = relationship("PostReaction", back_populates="user")
    comment_reactions = relationship("CommentReaction", back_populates="user")


class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date_created = Column(DateTime, default=func.now())
    title = Column(String)
    user = relationship("User", back_populates="posts")
    tags = relationship("Tag", secondary=post_tag, back_populates="posts")
    vaults = relationship("Vault", secondary=post_vault, back_populates="posts")
    files = relationship("PostFile", back_populates="post")
    comments = relationship("Comment", back_populates="post")
    reactions = relationship("PostReaction", back_populates="post", lazy="dynamic")

    @property
    def likes(self):
        return self.reactions.filter(PostReaction.type == "like").count()

    @property
    def dislikes(self):
        return self.reactions.filter(PostReaction.type == "dislike").count()


class PostFile(Base):
    __tablename__ = "post_files"
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    date_created = Column(DateTime, default=func.now(), nullable=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
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
    type = Column(String, nullable=False)
    user = relationship("User", back_populates="post_reactions")
    post = relationship("Post", back_populates="reactions")


class Vault(Base):
    __tablename__ = "vaults"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date_created = Column(DateTime, default=func.now())
    title = Column(String, nullable=False)
    user = relationship("User", back_populates="vaults")
    posts = relationship("Post", secondary=post_vault, back_populates="vaults")


class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, index=True)
    date_created = Column(DateTime, default=func.now())
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    posts = relationship("Post", secondary=post_tag, back_populates="tags")


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
        "CommentReaction", back_populates="Comment", lazy="dynamic"
    )

    @property
    def likes(self):
        return self.reactions.filter(CommentReaction.type == "like").count()

    @property
    def dislikes(self):
        return self.reactions.filter(CommentReaction.type == "dislike").count()


class CommentReaction(Base):
    __tablename__ = "comment_reactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    comment_id = Column(Integer, ForeignKey("comments.id"), nullable=False)
    date_created = Column(DateTime, default=func.now())
    type = Column(String, nullable=False)
    user = relationship("User", back_populates="comment_reactions")
    Comment = relationship("Comment", back_populates="reactions")
