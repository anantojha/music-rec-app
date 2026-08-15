"""
Music-provider abstraction layer.

The spec calls for Spotify support now with an abstraction layer for Apple Music
later. Every route/service that needs "the user's connected music provider" should
depend on this `MusicProviderClient` protocol, not on `SpotifyService` directly, so
adding Apple Music support later is a matter of implementing this interface and
registering it in `get_music_provider()` -- no changes needed to
recommendation_engine.py or the API layer.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ProviderTrack:
    """Normalized track shape returned by any music provider."""

    provider_track_id: str
    name: str
    artist_names: list[str]
    album_name: str | None = None
    release_year: int | None = None
    popularity: int | None = None
    tempo: float | None = None
    energy: float | None = None
    danceability: float | None = None
    acousticness: float | None = None
    genres: list[str] = field(default_factory=list)


@dataclass
class ProviderPlaylist:
    provider_playlist_id: str
    name: str
    track_count: int


class MusicProviderClient(ABC):
    """Every music-streaming integration (Spotify, Apple Music, ...) implements this."""

    provider_name: str

    @abstractmethod
    async def get_authorization_url(self, state: str) -> str:
        """Build the OAuth authorization URL the frontend redirects the user to."""

    @abstractmethod
    async def exchange_code_for_tokens(self, code: str) -> dict:
        """Exchange an OAuth `code` for access/refresh tokens. Returns provider-specific dict."""

    @abstractmethod
    async def list_playlists(self, access_token: str) -> list[ProviderPlaylist]:
        """List the current user's playlists."""

    @abstractmethod
    async def get_playlist_tracks(self, access_token: str, playlist_id: str) -> list[ProviderTrack]:
        """Fetch all tracks (with audio features where available) for one playlist."""

    @abstractmethod
    async def search_candidates(
        self, access_token: str, *, genres: list[str], search_terms: list[str], limit: int = 50
    ) -> list[ProviderTrack]:
        """Pipeline Step 3: retrieve candidate songs matching the taste profile."""
