from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

class Settings(BaseSettings):
    DATABASE_URL: str = os.environ.get("DATABASE_URL")
    RTSP_STREAM_URL: str = ""
    API_KEY: str = os.environ.get("API_KEY")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

settings = Settings()