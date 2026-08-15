"""
Sets required environment variables before any `app.*` module is imported, since
app.core.config.Settings() validates required fields (secret_key, database_url) at
import time. Individual tests never hit a real Postgres or external API -- see
each test module for what's mocked.
"""
import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db"
)
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("SPOTIFY_CLIENT_ID", "test-client-id")
os.environ.setdefault("SPOTIFY_CLIENT_SECRET", "test-client-secret")

import pytest  # noqa: E402
from cryptography.fernet import Fernet  # noqa: E402

os.environ.setdefault("TOKEN_ENCRYPTION_KEY", Fernet.generate_key().decode())


@pytest.fixture
def sample_provider_tracks():
    from app.services.music_provider import ProviderTrack

    return [
        ProviderTrack(
            provider_track_id="track_1",
            name="Midnight City",
            artist_names=["M83"],
            release_year=2011,
            popularity=78,
            tempo=105.0,
            energy=0.8,
            danceability=0.6,
            acousticness=0.05,
            genres=["synthpop", "electronic"],
        ),
        ProviderTrack(
            provider_track_id="track_2",
            name="Instant Crush",
            artist_names=["Daft Punk", "Julian Casablancas"],
            release_year=2013,
            popularity=82,
            tempo=120.0,
            energy=0.7,
            danceability=0.65,
            acousticness=0.1,
            genres=["electronic", "french house"],
        ),
    ]
