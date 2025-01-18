import os
from fastapi import FastAPI
from fastapi_pagination import add_pagination

from app.routers import post, auth, post_file, user, vault, comment, report, tag
from app.database import engine
from app.models import Base
from app.config import settings


app = FastAPI()
app.include_router(post.router)
app.include_router(post_file.router)
app.include_router(comment.router)
app.include_router(vault.router)
app.include_router(user.router)
app.include_router(report.router)
app.include_router(tag.router)
app.include_router(auth.router)

add_pagination(app)

Base.metadata.create_all(bind=engine)

if not os.path.exists(settings.UPLOAD_FOLDER):
    os.makedirs(settings.UPLOAD_FOLDER)
