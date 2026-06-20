from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Load settings from environment variables."""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://ugc_user:changeme@localhost:5432/ugc_video"

    # Supabase Auth
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""

    # Redis / Celery
    REDIS_URL: str = "redis://:changeme@localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://:changeme@localhost:6379/0"

    # Cloudflare R2
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = "ugc-video-creator"
    R2_ENDPOINT: str = ""

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # ====== Kie.ai — Unified API Key ======
    # Covers: LLM Chat, Video (Veo/Kling), Image (GPT Image 2), TTS (ElevenLabs)
    KIEAI_API_KEY: str = ""
    KIEAI_BASE_URL: str = "https://api.kie.ai"

    # LLM model slug for script generation (via Kie.ai's OpenAI-compatible endpoint)
    # Options: gemini-3-5-flash-openai, claude-sonnet-4-6, deepseek/deepseek-v4-flash, etc.
    KIEAI_LLM_MODEL: str = "gemini-3-5-flash-openai"

    # Default ElevenLabs voice ID for TTS (via Kie.ai)
    KIEAI_TTS_VOICE: str = "21m00Tcm4TlvDq8ikWAM"  # Rachel

    # Debug
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
