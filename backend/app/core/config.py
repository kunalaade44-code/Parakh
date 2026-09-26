import os
from pydantic_settings import BaseSettings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "dogfood.db")

class Settings(BaseSettings):
    PROJECT_NAME: str = "Dogfood Hackathon Platform"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-dogfood-key-2026-secure-isolated")
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")
    SESSION_COOKIE_NAME: str = "session"
    
    class Config:
        case_sensitive = True

settings = Settings()
