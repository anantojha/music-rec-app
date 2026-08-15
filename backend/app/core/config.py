"""
Centralized application configuration.

All runtime configuration is loaded from environment variables (see .env.example).
Using pydantic-settings gives us validation + type coercion for free, and a single
object (`settings`) that can be imported anywhere instead of scattering `os.environ`
calls throughout the codebase.
"""
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    environment: Literal["development", "staging", "production", "test"] = "development"
    secret_key: str
    access_token_expire_minutes: int = 60
    frontend_base_url: str = "http://localhost:5173"
    backend_base_url: str = "http://localhost:8000"

    # --- Database ---
    database_url: str

    # --- Spotify OAuth ---
    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    spotify_redirect_uri: str = "http://localhost:8000/spotify/callback"

    # --- Apple Music (future) ---
    apple_music_team_id: str = ""
    apple_music_key_id: str = ""
    apple_music_private_key: str = ""

    # --- OpenAI ---
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # --- Token encryption ---
    token_encryption_key: str = ""

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Settings are cached so the .env file / environment is only parsed once."""
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
