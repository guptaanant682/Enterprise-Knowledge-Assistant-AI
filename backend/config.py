from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional, List
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://localhost/enterprise_kb"

    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # ==================== AI API Configuration (Cascade Fallback) ====================
    # Priority 1: OpenAI Direct
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"

    # Priority 2: Anthropic Claude Direct
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"

    # Priority 3: OpenRouter (supports both OpenAI and Anthropic models)
    OPENROUTER_API_KEY: Optional[str] = None

    # Priority 4: Groq (Llama and other open models)
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_ALTERNATIVE_MODEL: Optional[str] = None  # e.g., "mixtral-8x7b-32768"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    # Legacy support (kept for backward compatibility)
    AI_PROVIDER: str = "cascade"  # "cascade" uses fallback system
    AI_MODEL: str = "gpt-4"  # Deprecated, use OPENAI_MODEL

    # AI General Configuration
    MAX_TOKENS: int = 1000
    TEMPERATURE: float = 0.7

    # ==================== Google OAuth Configuration ====================
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None

    # Environment detection (auto-configured)
    ENVIRONMENT: str = "development"  # or "production"

    @property
    def google_redirect_uri(self) -> str:
        """Auto-generate Google OAuth redirect URI based on environment"""
        if self.ENVIRONMENT == "production":
            return f"{self.FRONTEND_URL}/auth/google/callback"
        # Development: support both localhost and 127.0.0.1
        return "http://localhost:3000/auth/google/callback"

    @property
    def google_authorized_redirect_uris(self) -> List[str]:
        """List of all valid redirect URIs for Google OAuth"""
        uris = [
            "http://localhost:3000/auth/google/callback",
            "http://127.0.0.1:3000/auth/google/callback",
        ]
        if self.ENVIRONMENT == "production" and self.FRONTEND_URL:
            uris.append(f"{self.FRONTEND_URL}/auth/google/callback")
        return uris

    # ==================== Other Configuration ====================
    # Vector Database
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"

    # Redis
    REDIS_URL: Optional[str] = None

    # File Upload
    MAX_FILE_SIZE: int = 10485760  # 10MB
    UPLOAD_DIRECTORY: str = "./uploads"
    ALLOWED_FILE_TYPES: list = [".pdf", ".doc", ".docx", ".txt", ".md"]

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="allow"
    )

# Create settings instance
settings = Settings()

# Ensure required directories exist
os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)
os.makedirs(settings.CHROMA_PERSIST_DIRECTORY, exist_ok=True)