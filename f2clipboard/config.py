"""Application settings loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Runtime configuration driven by environment variables."""

    github_token: str | None = Field(default=None, alias="GITHUB_TOKEN")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    openai_model: str = Field(default="gpt-3.5-turbo", alias="OPENAI_MODEL")
    anthropic_model: str = Field(
        default="claude-3-haiku-20240307", alias="ANTHROPIC_MODEL"
    )
    codex_cookie: str | None = Field(default=None, alias="CODEX_COOKIE")
    log_size_threshold: int = Field(
        default=150_000,
        ge=0,
        alias="LOG_SIZE_THRESHOLD",
        description="Summarise logs larger than this many bytes",
    )

    class Config:
        env_file = ".env"
        case_sensitive = False
