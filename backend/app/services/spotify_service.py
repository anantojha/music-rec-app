"""
Spotify implementation of the MusicProviderClient interface.

Uses httpx.AsyncClient for all outbound calls so it plays nicely with FastAPI's
async request handling, and tenacity for retrying transient network failures.
"""
import base64
import urllib.parse

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.exceptions import UpstreamServiceError
from app.services.music_provider import MusicProviderClient, ProviderPlaylist, ProviderTrack

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"

_RETRYABLE = (httpx.TransportError, httpx.TimeoutException)


class SpotifyService(MusicProviderClient):
    provider_name = "spotify"

    def __init__(self, client: httpx.AsyncClient | None = None):
        self._client = client or httpx.AsyncClient(timeout=10.0)

    async def get_authorization_url(self, state: str) -> str:
        scopes = "playlist-read-private playlist-read-collaborative user-read-email"
        params = {
            "response_type": "code",
            "client_id": settings.spotify_client_id,
            "scope": scopes,
            "redirect_uri": settings.spotify_redirect_uri,
            "state": state,
        }
        return f"{SPOTIFY_AUTH_URL}?{urllib.parse.urlencode(params)}"

    @retry(
        retry=retry_if_exception_type(_RETRYABLE),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=4),
    )
    async def exchange_code_for_tokens(self, code: str) -> dict:
        basic_auth = base64.b64encode(
            f"{settings.spotify_client_id}:{settings.spotify_client_secret}".encode()
        ).decode()
        response = await self._client.post(
            SPOTIFY_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.spotify_redirect_uri,
            },
            headers={
                "Authorization": f"Basic {basic_auth}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        if response.status_code != 200:
            raise UpstreamServiceError(f"Spotify token exchange failed: {response.text}")
        return response.json()

    @retry(
        retry=retry_if_exception_type(_RETRYABLE),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=4),
    )
    async def list_playlists(self, access_token: str) -> list[ProviderPlaylist]:
        response = await self._client.get(
            f"{SPOTIFY_API_BASE}/me/playlists",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"limit": 50},
        )
        if response.status_code != 200:
            raise UpstreamServiceError(f"Spotify list playlists failed: {response.text}")

        return [
            ProviderPlaylist(
                provider_playlist_id=item["id"],
                name=item["name"],
                track_count=item["tracks"]["total"],
            )
            for item in response.json().get("items", [])
        ]

    async def get_playlist_tracks(self, access_token: str, playlist_id: str) -> list[ProviderTrack]:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await self._client.get(
            f"{SPOTIFY_API_BASE}/playlists/{playlist_id}/tracks",
            headers=headers,
            params={"limit": 100},
        )
        if response.status_code != 200:
            raise UpstreamServiceError(f"Spotify get playlist tracks failed: {response.text}")

        items = response.json().get("items", [])
        track_payloads = [item["track"] for item in items if item.get("track")]
        track_ids = [t["id"] for t in track_payloads if t.get("id")]
        features_by_id = await self._get_audio_features(access_token, track_ids)

        tracks = []
        for t in track_payloads:
            features = features_by_id.get(t["id"], {})
            tracks.append(
                ProviderTrack(
                    provider_track_id=t["id"],
                    name=t["name"],
                    artist_names=[a["name"] for a in t.get("artists", [])],
                    album_name=t.get("album", {}).get("name"),
                    release_year=_parse_year(t.get("album", {}).get("release_date")),
                    popularity=t.get("popularity"),
                    tempo=features.get("tempo"),
                    energy=features.get("energy"),
                    danceability=features.get("danceability"),
                    acousticness=features.get("acousticness"),
                )
            )
        return tracks

    async def search_candidates(
        self, access_token: str, *, genres: list[str], search_terms: list[str], limit: int = 50
    ) -> list[ProviderTrack]:
        headers = {"Authorization": f"Bearer {access_token}"}
        query_terms = search_terms or genres or ["popular"]
        query = " OR ".join(query_terms[:5])

        response = await self._client.get(
            f"{SPOTIFY_API_BASE}/search",
            headers=headers,
            params={"q": query, "type": "track", "limit": min(limit, 50)},
        )
        if response.status_code != 200:
            raise UpstreamServiceError(f"Spotify search failed: {response.text}")

        items = response.json().get("tracks", {}).get("items", [])
        return [
            ProviderTrack(
                provider_track_id=t["id"],
                name=t["name"],
                artist_names=[a["name"] for a in t.get("artists", [])],
                album_name=t.get("album", {}).get("name"),
                release_year=_parse_year(t.get("album", {}).get("release_date")),
                popularity=t.get("popularity"),
            )
            for t in items
        ]

    async def _get_audio_features(self, access_token: str, track_ids: list[str]) -> dict[str, dict]:
        if not track_ids:
            return {}
        response = await self._client.get(
            f"{SPOTIFY_API_BASE}/audio-features",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"ids": ",".join(track_ids[:100])},
        )
        if response.status_code != 200:
            # Non-fatal: recommendation engine can degrade gracefully without audio features.
            return {}
        return {f["id"]: f for f in response.json().get("audio_features", []) if f}


def _parse_year(release_date: str | None) -> int | None:
    if not release_date:
        return None
    try:
        return int(release_date[:4])
    except ValueError:
        return None
