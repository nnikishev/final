from pathlib import Path
import os
from pydantic_settings import BaseSettings

from dotenv import load_dotenv
from sqlalchemy import URL

BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BASE_DIR / "schema_editor"

load_dotenv(BASE_DIR / ".env")


class DBSettings(BaseSettings):
    DB_HOST: str | None = os.environ.get("DB_HOST")
    DB_PORT: str | None = os.environ.get("DB_PORT")
    DB_NAME: str | None = os.environ.get("DB_NAME")
    DB_USER: str | None = os.environ.get("DB_USER")
    DB_PASSWORD: str | None = os.environ.get("DB_PASSWORD")
    DATABASE_URL: str | URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


class RedisSettings(BaseSettings):
    HOST: str = "localhost"
    PORT: int = 6379
    CHANNEL: str = "cv_events"
    CUTTING_PLAN_CHANNEL: str = "cutting_plans"
    DLQ_CHANNEL: str = "statistics_dlq"


class Settings(BaseSettings):
    db: DBSettings = DBSettings()
    redis: RedisSettings = RedisSettings()


settings = Settings()