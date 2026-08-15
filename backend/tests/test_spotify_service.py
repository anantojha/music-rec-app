import httpx
import pytest
import respx

from app.core.exceptions import UpstreamServiceError
from app.services.spotify_service import SPOTIFY_API_BASE, SPOTIFY_TOKEN_URL, SpotifyService


@pytest.fixture
def spotify_service():
    return SpotifyService(client=httpx.AsyncClient())


class TestGetAuthorizationUrl:
    async def test_includes_required_params(self, spotify_service):
        url = await spotify_service.get_authorization_url(state="xyz")
        assert "response_type=code" in url
        assert "state=xyz" in url
        assert "accounts.spotify.com/authorize" in url


class TestExchangeCodeForTokens:
    @respx.mock
    async def test_success(self, spotify_service):
        respx.post(SPOTIFY_TOKEN_URL).mock(
            return_value=httpx.Response(
                200, json={"access_token": "at_123", "refresh_token": "rt_456", "expires_in": 3600}
            )
        )
        tokens = await spotify_service.exchange_code_for_tokens("auth_code")
        assert tokens["access_token"] == "at_123"

    @respx.mock
    async def test_failure_raises_upstream_error(self, spotify_service):
        respx.post(SPOTIFY_TOKEN_URL).mock(
            return_value=httpx.Response(400, json={"error": "invalid_grant"})
        )
        with pytest.raises(UpstreamServiceError):
            await spotify_service.exchange_code_for_tokens("bad_code")


class TestListPlaylists:
    @respx.mock
    async def test_parses_playlists(self, spotify_service):
        respx.get(f"{SPOTIFY_API_BASE}/me/playlists").mock(
            return_value=httpx.Response(
                200,
                json={
                    "items": [
                        {"id": "pl_1", "name": "Chill Vibes", "tracks": {"total": 42}},
                        {"id": "pl_2", "name": "Workout", "tracks": {"total": 20}},
                    ]
                },
            )
        )
        playlists = await spotify_service.list_playlists("fake_token")
        assert len(playlists) == 2
        assert playlists[0].provider_playlist_id == "pl_1"
        assert playlists[0].track_count == 42


class TestGetPlaylistTracks:
    @respx.mock
    async def test_merges_audio_features(self, spotify_service):
        respx.get(f"{SPOTIFY_API_BASE}/playlists/pl_1/tracks").mock(
            return_value=httpx.Response(
                200,
                json={
                    "items": [
                        {
                            "track": {
                                "id": "t1",
                                "name": "Song One",
                                "artists": [{"name": "Artist A"}],
                                "album": {"name": "Album A", "release_date": "2020-05-01"},
                                "popularity": 55,
                            }
                        }
                    ]
                },
            )
        )
        respx.get(f"{SPOTIFY_API_BASE}/audio-features").mock(
            return_value=httpx.Response(
                200, json={"audio_features": [{"id": "t1", "tempo": 128.0, "energy": 0.9, "danceability": 0.5, "acousticness": 0.1}]}
            )
        )

        tracks = await spotify_service.get_playlist_tracks("fake_token", "pl_1")

        assert len(tracks) == 1
        assert tracks[0].name == "Song One"
        assert tracks[0].tempo == 128.0
        assert tracks[0].release_year == 2020

    @respx.mock
    async def test_gracefully_degrades_when_audio_features_fail(self, spotify_service):
        respx.get(f"{SPOTIFY_API_BASE}/playlists/pl_1/tracks").mock(
            return_value=httpx.Response(
                200,
                json={"items": [{"track": {"id": "t1", "name": "Song One", "artists": [], "album": {}}}]},
            )
        )
        respx.get(f"{SPOTIFY_API_BASE}/audio-features").mock(return_value=httpx.Response(403))

        tracks = await spotify_service.get_playlist_tracks("fake_token", "pl_1")

        assert len(tracks) == 1
        assert tracks[0].tempo is None  # degraded gracefully instead of raising
