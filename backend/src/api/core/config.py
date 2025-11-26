import os
from functools import lru_cache
from pydantic import BaseModel, Field


class Settings(BaseModel):
    """
    Application settings loaded from environment variables with safe defaults.
    """

    nasa_api_key: str = Field(default_factory=lambda: os.getenv("NASA_API_KEY", "DEMO_KEY"))
    database_url: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./apod_cache.db"))
    port: int = Field(default_factory=lambda: int(os.getenv("PORT", "3001")))

    # CORS related hints (optional)
    frontend_url: str | None = Field(default_factory=lambda: os.getenv("REACT_APP_FRONTEND_URL"))
    backend_url: str | None = Field(default_factory=lambda: os.getenv("REACT_APP_BACKEND_URL"))
    api_base: str | None = Field(default_factory=lambda: os.getenv("REACT_APP_API_BASE"))


# PUBLIC_INTERFACE
@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings instance constructed from environment variables.
    """
    return Settings()
