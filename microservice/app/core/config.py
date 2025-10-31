"""Application configuration using Pydantic V2 settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application Settings
    app_name: str = Field(default="GenAI Document Mapping Service")
    app_version: str = Field(default="0.1.0")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # API Settings
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_reload: bool = Field(default=False)

    # PostgreSQL Database
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)
    postgres_db: str = Field(default="document_mapping")
    postgres_user: str = Field(default="postgres")
    postgres_password: str = Field(default="postgres")
    database_url: str | None = Field(default=None)

    # pgvector settings
    pgvector_dimension: int = Field(default=3072)
    pgvector_ivfflat_lists: int = Field(default=100)  # For IVFFlat index

    # OpenAI Settings
    openai_api_key: str | None = Field(default=None)
    openai_model: str = Field(default="gpt-4-turbo-preview")
    openai_embedding_model: str = Field(default="text-embedding-3-large")
    openai_embedding_dimensions: int = Field(default=3072)

    # Anthropic Settings
    anthropic_api_key: str | None = Field(default=None)
    anthropic_model: str = Field(default="claude-3-sonnet-20240229")

    # LLM Provider
    llm_provider: Literal["openai", "anthropic"] = Field(default="openai")

    # Document Processing Settings
    chunk_size: int = Field(default=1000, ge=100, le=10000)
    chunk_overlap: int = Field(default=200, ge=0, le=1000)
    max_file_size_mb: int = Field(default=50, ge=1, le=500)

    # Mind Map Generation Settings
    max_topics: int = Field(default=10, ge=1, le=50)
    max_subtopics_per_topic: int = Field(default=5, ge=1, le=20)
    mind_map_depth: int = Field(default=3, ge=1, le=5)

    # Upload Settings
    upload_dir: str = Field(default="./uploads")
    temp_dir: str = Field(default="./temp")

    # AWS/S3 Settings
    aws_region: str = Field(default="us-east-1")
    aws_access_key_id: str | None = Field(default=None)
    aws_secret_access_key: str | None = Field(default=None)
    aws_session_token: str | None = Field(default=None)
    s3_bucket_name: str | None = Field(default=None, validation_alias=AliasChoices("S3_BUCKET_NAME", "S3_BUCKET"))
    s3_endpoint_url: str | None = Field(default=None)
    s3_prefix: str = Field(default="documents/")
    use_s3_storage: bool = Field(default=True)

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str | None, values) -> str:
        """Construct database URL if not provided."""
        if v:
            return v
        # Access raw data since we're in before mode
        return (
            f"postgresql+psycopg://{values.data.get('postgres_user')}:"
            f"{values.data.get('postgres_password')}@"
            f"{values.data.get('postgres_host')}:{values.data.get('postgres_port')}/"
            f"{values.data.get('postgres_db')}"
        )

    @property
    def max_file_size_bytes(self) -> int:
        """Convert max file size from MB to bytes."""
        return self.max_file_size_mb * 1024 * 1024


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

