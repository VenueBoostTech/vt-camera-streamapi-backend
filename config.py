import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./visiontrack.db")
    RTSP_STREAM_URL: str = os.getenv("RTSP_STREAM_URL", "")
    API_KEY: str = os.getenv("API_KEY", "your-api-key")

    class Config:
        env_file = ".env"

settings = Settings()