from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://baoyan:baoyan_secret@localhost:5432/baoyan_db"
    REDIS_URL: str = "redis://localhost:6379"
    # LLM config — OpenRouter (OpenAI-compatible)
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_MODEL: str = "deepseek/deepseek-chat-v3-0324"
    # Legacy alias
    ANTHROPIC_API_KEY: str = ""
    UPLOAD_DIR: str = "./data/uploads"
    RAW_DIR: str = "./data/raw"
    PROCESSED_DIR: str = "./data/processed"
    APP_ENV: str = "development"
    SECRET_KEY: str = "change-me-in-production"
    MAX_FILE_SIZE_MB: int = 50

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
