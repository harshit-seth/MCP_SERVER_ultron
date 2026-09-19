"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated runtime configuration for the MCP server."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "web-search-mcp"
    version: str = "0.1.0"
    host: str = "0.0.0.0"
    port: int = Field(default=8080, ge=1, le=65535)
    mcp_transport: Literal["stdio", "sse", "streamable-http"] = "streamable-http"

    search_api_key: str | None = None
    search_api_url: AnyHttpUrl = "https://api.search.brave.com/res/v1/web/search"
    request_timeout_seconds: float = Field(default=15.0, gt=0, le=120)
    max_fetch_bytes: int = Field(default=2_000_000, ge=10_000, le=10_000_000)
    max_response_chars: int = Field(default=20_000, ge=1_000, le=100_000)
    max_redirects: int = Field(default=3, ge=0, le=10)
    default_max_results: int = Field(default=5, ge=1, le=10)

    @property
    def search_endpoint(self) -> str:
        """Return the configured search endpoint as a plain string."""

        return str(self.search_api_url)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and cache validated application settings."""

    return Settings()