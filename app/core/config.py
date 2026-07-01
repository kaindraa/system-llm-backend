from pydantic_settings import BaseSettings
from typing import List, Optional
import json

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "system_llm"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 1 day = 24 hours * 60 minutes

    # Application
    PROJECT_NAME: str = "System LLM"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # CORS
    BACKEND_CORS_ORIGINS: str = '["http://localhost:3000","http://localhost:3001","http://localhost:8000"]'
    # Regex for origins not known up-front (e.g. Vercel per-deployment URLs).
    # Example: https://system-llm-frontend.*\.vercel\.app
    BACKEND_CORS_ORIGIN_REGEX: str = ""

    # LLM Configuration
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    DEFAULT_LLM_MODEL: str = "gpt-4-mini"

    # Cloud Storage Configuration
    STORAGE_TYPE: str = "local"  # Options: "local", "gcs", "supabase"
    FILE_STORAGE_PATH: str = "file_to_ingest"  # Path to local file storage directory (relative or absolute)
    GCS_BUCKET_NAME: str = "system-llm-storage"
    GCS_PROJECT_ID: str = "system-llm"
    GCS_CREDENTIALS_PATH: Optional[str] = None  # Path to JSON credentials file (optional, uses ADC/IAM if None)

    # Supabase Storage Configuration (required if STORAGE_TYPE=supabase)
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""  # service_role key (bypass RLS) — backend only, never expose
    SUPABASE_STORAGE_BUCKET: str = "documents"

    # Sentry error monitoring (empty DSN disables Sentry, e.g. local dev)
    SENTRY_DSN: str = ""
    SENTRY_ENVIRONMENT: str = "production"
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1

    # Ingestion recovery on startup
    # Default is safe for production: recover stale status, but do not restart
    # heavy ingestion work automatically on web app boot.
    INGESTION_REQUEUE_ORPHANS_ON_STARTUP: bool = False
    INGESTION_HEARTBEAT_ENABLED: bool = False

    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from JSON string"""
        if not self.BACKEND_CORS_ORIGINS or self.BACKEND_CORS_ORIGINS.strip() == "":
            return ["*"]  # Default to allow all if empty
        try:
            return json.loads(self.BACKEND_CORS_ORIGINS)
        except json.JSONDecodeError:
            # Fallback: if not valid JSON, treat as single origin
            return [self.BACKEND_CORS_ORIGINS]

    class Config:
        env_file = ".env"  # Changed from .env.local to .env for flexibility
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env

settings = Settings()
