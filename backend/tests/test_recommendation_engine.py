import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import UpstreamServiceError
from app.schemas.recommendation import TasteProfile
from app.services.music_provider import ProviderTrack
from app.services.openai_service import RankedTrack
from app.services.recommendation_engine import RecommendationEngine


def _make_track_row(track_id, provider_track_id):
    row = MagicMock()
    row.id = track_id
    row.provider_track_id = provider_track_id
    return row


@pytest.fixture
def mock_playlist():
    playlist = MagicMock()
    playlist.id = uuid.uuid4()
    playlist.name = "Road Trip Mix"
    return playlist


@pytest.fixture
def engine_deps():
    music_provider = AsyncMock()
    music_provider.provider_name = "spotify"
    openai_service = AsyncMock()
    playlist_repo = AsyncMock()
    track_repo = AsyncMock()
    recommendation_repo = AsyncMock()
    return music_provider, openai_service, playlist_repo, track_repo, recommendation_repo


class TestRecommendationEngine:
    async def test_full_pipeline_happy_path(self, mock_playlist, engine_deps, sample_provider_tracks):
        music_provider, openai_service, playlist_repo, track_repo, recommendation_repo = engine_deps

        taste_profile = TasteProfile(
            genres=["electronic"], mood=["energetic"], energy="high",
            eras=["2010s"], recommended_search_terms=["synthpop"],
        )
        openai_service.build_taste_profile.return_value = taste_profile

        candidates = [
            ProviderTrack(provider_track_id="cand_1", name="New Song", artist_names=["Artist X"]),
            ProviderTrack(provider_track_id="cand_2", name="Another Song", artist_names=["Artist Y"]),
        ]
        music_provider.search_candidates.return_value = candidates

        ranked = [
            RankedTrack(track_id="cand_1", confidence_score=0.95, explanation="High energy match"),
            RankedTrack(track_id="cand_2", confidence_score=0.80, explanation="Genre match"),
        ]
        openai_service.rank_candidates.return_value = ranked

        track_repo.get_or_create_from_provider.side_effect = [
            _make_track_row(uuid.uuid4(), "cand_1"),
            _make_track_row(uuid.uuid4(), "cand_2"),
        ]

        engine = RecommendationEngine(
            music_provider=music_provider,
            openai_service=openai_service,
            playlist_repo=playlist_repo,
            track_repo=track_repo,
            recommendation_repo=recommendation_repo,
        )

        result = await engine.generate(
            access_token="fake-token", playlist=mock_playlist, source_tracks=sample_provider_tracks
        )

        assert result.taste_profile == taste_profile
        assert len(result.ranked_items) == 2
        assert result.ranked_items[0]["rank"] == 1
        assert result.ranked_items[0]["confidence_score"] == 0.95
        openai_service.build_taste_profile.assert_awaited_once_with(mock_playlist.name, sample_provider_tracks)

    async def test_empty_source_playlist_raises(self, mock_playlist, engine_deps):
        music_provider, openai_service, playlist_repo, track_repo, recommendation_repo = engine_deps
        engine = RecommendationEngine(
            music_provider, openai_service, playlist_repo, track_repo, recommendation_repo
        )

        with pytest.raises(UpstreamServiceError, match="no tracks"):
            await engine.generate(access_token="token", playlist=mock_playlist, source_tracks=[])

    async def test_excludes_tracks_already_in_source_playlist(
        self, mock_playlist, engine_deps, sample_provider_tracks
    ):
        music_provider, openai_service, playlist_repo, track_repo, recommendation_repo = engine_deps
        openai_service.build_taste_profile.return_value = TasteProfile()

        # One candidate duplicates a source track (track_1); it must be filtered out
        # before ever reaching GPT ranking or being recommended back to the user.
        duplicate_candidate = ProviderTrack(
            provider_track_id="track_1", name="Midnight City", artist_names=["M83"]
        )
        new_candidate = ProviderTrack(provider_track_id="cand_new", name="Fresh Pick", artist_names=["Artist Z"])
        music_provider.search_candidates.return_value = [duplicate_candidate, new_candidate]

        openai_service.rank_candidates.return_value = [
            RankedTrack(track_id="cand_new", confidence_score=0.7, explanation="new")
        ]
        track_repo.get_or_create_from_provider.return_value = _make_track_row(uuid.uuid4(), "cand_new")

        engine = RecommendationEngine(
            music_provider, openai_service, playlist_repo, track_repo, recommendation_repo
        )
        await engine.generate(access_token="token", playlist=mock_playlist, source_tracks=sample_provider_tracks)

        # Verify GPT ranking was only ever offered the non-duplicate candidate.
        call_args = openai_service.rank_candidates.await_args
        passed_candidates = call_args.args[1]
        assert all(c.provider_track_id != "track_1" for c in passed_candidates)

    async def test_no_candidates_found_raises(self, mock_playlist, engine_deps, sample_provider_tracks):
        music_provider, openai_service, playlist_repo, track_repo, recommendation_repo = engine_deps
        openai_service.build_taste_profile.return_value = TasteProfile()
        music_provider.search_candidates.return_value = []

        engine = RecommendationEngine(
            music_provider, openai_service, playlist_repo, track_repo, recommendation_repo
        )

        with pytest.raises(UpstreamServiceError, match="No candidate songs"):
            await engine.generate(access_token="token", playlist=mock_playlist, source_tracks=sample_provider_tracks)

    async def test_gpt_returns_no_valid_rankings_raises(
        self, mock_playlist, engine_deps, sample_provider_tracks
    ):
        music_provider, openai_service, playlist_repo, track_repo, recommendation_repo = engine_deps
        openai_service.build_taste_profile.return_value = TasteProfile()
        music_provider.search_candidates.return_value = [
            ProviderTrack(provider_track_id="cand_1", name="Song", artist_names=["Artist"])
        ]
        openai_service.rank_candidates.return_value = []

        engine = RecommendationEngine(
            music_provider, openai_service, playlist_repo, track_repo, recommendation_repo
        )

        with pytest.raises(UpstreamServiceError, match="did not return"):
            await engine.generate(access_token="token", playlist=mock_playlist, source_tracks=sample_provider_tracks)
