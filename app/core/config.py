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
    BACKEND_CORS_ORIGINS: str = '["http://localhost:3000","http://localhost:8000"]'

    # LLM Configuration
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    DEFAULT_LLM_MODEL: str = "gpt-5-mini"

    # Cloud Storage Configuration
    STORAGE_TYPE: str = "local"  # Options: "local", "gcs"
    GCS_BUCKET_NAME: str = "system-llm-storage"
    GCS_PROJECT_ID: str = "system-llm"
    GCS_CREDENTIALS_PATH: Optional[str] = None  # Path to JSON credentials file (optional, uses ADC/IAM if None)

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
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env

settings = Settings()

# DEBUG: Log settings on startup
print(f"[DEBUG] [Config] Settings initialized")
print(f"[DEBUG] [Config] SECRET_KEY length: {len(settings.SECRET_KEY)}")
print(f"[DEBUG] [Config] SECRET_KEY: {settings.SECRET_KEY}")
print(f"[DEBUG] [Config] SECRET_KEY hex: {settings.SECRET_KEY.encode().hex()}")
print(f"[DEBUG] [Config] DATABASE_URL: {settings.DATABASE_URL[:50]}...")
print(f"[DEBUG] [Config] ALGORITHM: {settings.ALGORITHM}")
