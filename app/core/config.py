"""
Funnel Aether - Core Configuration
Uses Pydantic Settings for clean environment variable management.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    # Project
    PROJECT_NAME: str = "Funnel Aether"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "AI-powered all-in-one marketing operating system for SMEs. Human-AI hybrid."

    # Environment
    ENVIRONMENT: str = "development"  # development | staging | production
    DEBUG: bool = True

    # Database (SQLite for MVP, easy to switch to Postgres)
    DATABASE_URL: str = "sqlite:///./funnel_aether.db"
    # For production: "postgresql://user:pass@localhost/funnel_aether"

    # AI / LLM Configuration
    # Primary LLM for content & reasoning (we can make this configurable per user later)
    DEFAULT_LLM_PROVIDER: str = "anthropic"  # or "openai" or "grok"
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GROK_API_KEY: str = ""  # if using xAI Grok

    # RAG / Vector Store (Chroma for MVP - local & simple)
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"
    BRAND_VOICE_COLLECTION: str = "brand_voice"

    # Security (for later auth)
    SECRET_KEY: str = "change-this-in-production-please"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
