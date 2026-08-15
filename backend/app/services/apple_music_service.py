"""
Apple Music implementation stub.

Not wired into the API yet (MVP is Spotify-only per the spec), but implementing
`MusicProviderClient` now proves the abstraction holds: recommendation_engine.py
and the API routes never import SpotifyService directly, so swapping/adding this
provider later is additive, not a rewrite. Fill in real MusicKit JWT signing +
Apple Music API calls (developer token via ES256, storefront lookups, etc.) when
Apple Music support is prioritized.
"""
from app.services.music_provider import MusicProviderClient, ProviderPlaylist, ProviderTrack


class AppleMusicService(MusicProviderClient):
    provider_name = "apple_music"

    async def get_authorization_url(self, state: str) -> str:
        raise NotImplementedError("Apple Music support is planned but not yet implemented.")

    async def exchange_code_for_tokens(self, code: str) -> dict:
        raise NotImplementedError("Apple Music support is planned but not yet implemented.")

    async def list_playlists(self, access_token: str) -> list[ProviderPlaylist]:
        raise NotImplementedError("Apple Music support is planned but not yet implemented.")

    async def get_playlist_tracks(self, access_token: str, playlist_id: str) -> list[ProviderTrack]:
        raise NotImplementedError("Apple Music support is planned but not yet implemented.")

    async def search_candidates(
        self, access_token: str, *, genres: list[str], search_terms: list[str], limit: int = 50
    ) -> list[ProviderTrack]:
        raise NotImplementedError("Apple Music support is planned but not yet implemented.")
