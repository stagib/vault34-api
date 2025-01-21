import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_URL: str
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    UPLOAD_FOLDER: str = os.path.join(os.getcwd(), "uploads")
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100 MB
    ALLOWED_IMAGE_TYPES: list = [
        "image/jpeg",
        "image/png",
        "image/gif",
    ]
    ALLOWED_VIDEO_TYPES: list = [
        "video/mp4",
        "video/avi",
        "video/mkv",
    ]

    class Config:
        env_file = ".env"


settings = Settings()
