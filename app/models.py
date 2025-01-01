from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date_created = Column(DateTime, default=func.now())
    title = Column(String)
    user = relationship("User", back_populates="posts")
    files = relationship("PostFile", back_populates="post")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    date_created = Column(DateTime, default=func.now(), nullable=True)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    posts = relationship("Post", back_populates="user")


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
