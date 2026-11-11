from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./brewwise.db",
        description="Async database connection string"
    )

    # Redis Cache & Broker
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )

    # Storage
    STORAGE_PROVIDER: str = Field(default="local", description="Storage provider (local or s3)")
    LOCAL_STORAGE_DIR: str = Field(default="./uploads", description="Directory for local image uploads")
    S3_ENDPOINT: str = Field(default="http://localhost:9000", description="S3 / MinIO endpoint")
    S3_BUCKET: str = Field(default="brewwise-images", description="Storage bucket name")
    S3_ACCESS_KEY: Optional[str] = Field(default=None, description="S3 access key")
    S3_SECRET_KEY: Optional[str] = Field(default=None, description="S3 secret key")

    # AI & Vision
    VISION_PROVIDER: str = Field(default="gemini", description="Vision extraction provider")
    LLM_PROVIDER: str = Field(default="gemini", description="LLM synthesis provider")
    LLM_MODEL: str = Field(default="gemini-2.5-flash", description="LLM model identifier")
    EMBEDDING_PROVIDER: str = Field(default="gemini", description="Embeddings provider")
    EMBEDDING_MODEL: str = Field(default="text-embedding-004", description="Embedding model name")
    GOOGLE_API_KEY: Optional[str] = Field(default=None, description="Google Gemini API key")

    # Search & Discovery
    SEARCH_PROVIDER: str = Field(default="mock", description="Search provider (google, tavily, mock)")
    SEARCH_API_KEY: Optional[str] = Field(default=None, description="Search API key")
    GOOGLE_SEARCH_CX: Optional[str] = Field(default=None, description="Google Custom Search Engine ID")
    TAVILY_API_KEY: Optional[str] = Field(default=None, description="Tavily API key")
    LIVE_DISCOVERY_ENABLED: bool = Field(default=True, description="Enable inline web discovery")
    LIVE_DISCOVERY_PERSIST: bool = Field(default=True, description="Persist discovered sources into KB")
    LIVE_DISCOVERY_TOTAL_TIMEOUT: float = Field(default=15.0, description="Total budget in seconds for live discovery")
    LIVE_DISCOVERY_PER_URL_TIMEOUT: float = Field(default=6.0, description="Per-URL fetch timeout in seconds")
    LIVE_DISCOVERY_RATE_LIMIT: int = Field(default=10, description="Max queries per minute")
    LIVE_DISCOVERY_MAX_URLS: int = Field(default=5, description="Max URLs to fetch per scan")

    # Security & Limits
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
        description="Allowed CORS origins"
    )
    MAX_UPLOAD_SIZE_MB: int = Field(default=10, description="Max upload file size in megabytes")
    LOG_LEVEL: str = Field(default="INFO", description="Log level")
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


settings = Settings()
