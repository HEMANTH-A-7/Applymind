"""
ApplyMind AI — Core Settings
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App environment
    environment: str = "development"

    # Groq (primary LLM)
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # Gemini (fallback LLM — used when Groq errors or rate-limits)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # Adzuna (job listings API)
    adzuna_app_id: str = ""
    adzuna_app_key: str = ""

    # Database
    database_url: str = "postgresql+asyncpg://applymind:applymind123@localhost:5432/applymind"
    redis_url: str = "redis://localhost:6379/0"

    # Security
    secret_key: str = "applymind-super-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    encryption_key: str = ""
    sentry_dsn: str = ""

    # Email
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""

    # CAPTCHA
    twocaptcha_api_key: str = ""

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = True
    daily_app_limit: int = 50
    auto_apply_threshold: int = 65

    # Firebase
    firebase_project_id: str = ""
    firebase_service_account_path: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
