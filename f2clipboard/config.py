"""Application settings loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Runtime configuration driven by environment variables."""

    github_token: str | None = Field(default=None, alias="GITHUB_TOKEN")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    codex_cookie: str | None = Field(default=None, alias="CODEX_COOKIE")
    log_size_threshold: int = Field(default=150000, alias="LOG_SIZE_THRESHOLD")

    class Config:
        env_file = ".env"
        case_sensitive = False
