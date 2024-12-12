from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./visiontrack.db"
    RTSP_STREAM_URL: str = ""
    API_KEY: str = "your-api-key"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()