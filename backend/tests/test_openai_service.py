import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import UpstreamServiceError
from app.services.openai_service import OpenAIService
from app.services.music_provider import ProviderTrack


def _fake_openai_response(content: dict) -> SimpleNamespace:
    """Mimics the shape of an openai.types.chat.ChatCompletion response."""
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(content)))]
    )


@pytest.fixture
def mock_openai_client():
    client = AsyncMock()
    client.chat.completions.create = AsyncMock()
    return client


class TestBuildTasteProfile:
    async def test_returns_valid_taste_profile(self, mock_openai_client, sample_provider_tracks):
        mock_openai_client.chat.completions.create.return_value = _fake_openai_response(
            {
                "genres": ["electronic", "synthpop"],
                "mood": ["energetic", "nostalgic"],
                "energy": "high",
                "eras": ["2010s"],
                "recommended_search_terms": ["french house", "dream pop"],
            }
        )
        service = OpenAIService(client=mock_openai_client)

        profile = await service.build_taste_profile("Late Night Drive", sample_provider_tracks)

        assert profile.energy == "high"
        assert "electronic" in profile.genres
        mock_openai_client.chat.completions.create.assert_awaited_once()

    async def test_invalid_energy_value_raises(self, mock_openai_client, sample_provider_tracks):
        mock_openai_client.chat.completions.create.return_value = _fake_openai_response(
            {
                "genres": [],
                "mood": [],
                "energy": "extremely-high",  # not one of low|medium|high
                "eras": [],
                "recommended_search_terms": [],
            }
        )
        service = OpenAIService(client=mock_openai_client)

        with pytest.raises(UpstreamServiceError):
            await service.build_taste_profile("Playlist", sample_provider_tracks)

    async def test_non_json_response_raises(self, mock_openai_client, sample_provider_tracks):
        mock_openai_client.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="not json at all"))]
        )
        service = OpenAIService(client=mock_openai_client)

        with pytest.raises(UpstreamServiceError):
            await service.build_taste_profile("Playlist", sample_provider_tracks)


class TestRankCandidates:
    async def test_filters_out_hallucinated_track_ids(self, mock_openai_client, sample_provider_tracks):
        from app.schemas.recommendation import TasteProfile

        mock_openai_client.chat.completions.create.return_value = _fake_openai_response(
            {
                "recommendations": [
                    {"track_id": "track_1", "confidence_score": 0.9, "explanation": "Matches energy"},
                    {"track_id": "track_does_not_exist", "confidence_score": 0.5, "explanation": "hallucinated"},
                ]
            }
        )
        service = OpenAIService(client=mock_openai_client)
        profile = TasteProfile(energy="high")

        ranked = await service.rank_candidates(profile, sample_provider_tracks)

        assert len(ranked) == 1
        assert ranked[0].track_id == "track_1"

    async def test_caps_results_at_ten(self, mock_openai_client, sample_provider_tracks):
        from app.schemas.recommendation import TasteProfile

        many_candidates = sample_provider_tracks + [
            ProviderTrack(provider_track_id=f"track_{i}", name=f"Song {i}", artist_names=["Artist"])
            for i in range(3, 15)
        ]
        recs = [
            {"track_id": t.provider_track_id, "confidence_score": 0.5, "explanation": "ok"}
            for t in many_candidates
        ]
        mock_openai_client.chat.completions.create.return_value = _fake_openai_response(
            {"recommendations": recs}
        )
        service = OpenAIService(client=mock_openai_client)
        profile = TasteProfile(energy="medium")

        ranked = await service.rank_candidates(profile, many_candidates)

        assert len(ranked) == 10
