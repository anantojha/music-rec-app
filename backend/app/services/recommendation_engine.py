"""
The core recommendation pipeline, matching the 4 steps in the project spec:

  1. Build playlist profile   -> extract genres/artists/years/audio features from the
                                  playlist's tracks (done by the music provider + this module)
  2. GPT prompt                -> OpenAIService.build_taste_profile()
  3. Candidate retrieval       -> MusicProviderClient.search_candidates() (~50 candidates)
  4. GPT ranking                -> OpenAIService.rank_candidates() (top 10 + explanations)

This module only depends on the MusicProviderClient abstraction, never on
SpotifyService directly, so it works unmodified once Apple Music is implemented.
"""
from dataclasses import dataclass

from app.core.exceptions import UpstreamServiceError
from app.db.repositories import PlaylistRepository, RecommendationRepository, TrackRepository
from app.models.playlist import Playlist
from app.schemas.recommendation import TasteProfile
from app.services.music_provider import MusicProviderClient, ProviderTrack
from app.services.openai_service import OpenAIService

CANDIDATE_POOL_SIZE = 50
TOP_N_RECOMMENDATIONS = 10


@dataclass
class RecommendationResult:
    taste_profile: TasteProfile
    ranked_items: list[dict]  # [{track_id, rank, confidence_score, explanation}]


class RecommendationEngine:
    def __init__(
        self,
        music_provider: MusicProviderClient,
        openai_service: OpenAIService,
        playlist_repo: PlaylistRepository,
        track_repo: TrackRepository,
        recommendation_repo: RecommendationRepository,
    ):
        self._music_provider = music_provider
        self._openai = openai_service
        self._playlist_repo = playlist_repo
        self._track_repo = track_repo
        self._recommendation_repo = recommendation_repo

    async def generate(
        self, *, access_token: str, playlist: Playlist, source_tracks: list[ProviderTrack]
    ) -> RecommendationResult:
        if not source_tracks:
            raise UpstreamServiceError("Playlist has no tracks to build a taste profile from.")

        # Step 1 (extraction) happens implicitly: `source_tracks` already carries
        # genres/artists/years/audio-features pulled by the music provider.

        # Step 2: GPT builds a structured taste profile from the playlist.
        taste_profile = await self._openai.build_taste_profile(playlist.name, source_tracks)

        # Step 3: retrieve ~50 candidate songs matching the profile.
        candidates = await self._music_provider.search_candidates(
            access_token,
            genres=taste_profile.genres,
            search_terms=taste_profile.recommended_search_terms,
            limit=CANDIDATE_POOL_SIZE,
        )
        # Never recommend songs already in the source playlist.
        source_ids = {t.provider_track_id for t in source_tracks}
        candidates = [c for c in candidates if c.provider_track_id not in source_ids]
        if not candidates:
            raise UpstreamServiceError("No candidate songs found for this taste profile.")

        # Step 4: GPT ranks candidates down to the top 10 with explanations.
        ranked = await self._openai.rank_candidates(taste_profile, candidates)
        if not ranked:
            raise UpstreamServiceError("GPT did not return any valid ranked recommendations.")

        candidates_by_id = {c.provider_track_id: c for c in candidates}
        ranked_items = []
        for rank, item in enumerate(ranked[:TOP_N_RECOMMENDATIONS], start=1):
            provider_track = candidates_by_id[item.track_id]
            track = await self._track_repo.get_or_create_from_provider(
                provider=self._music_provider.provider_name,
                provider_track_id=provider_track.provider_track_id,
                name=provider_track.name,
                artist_names=provider_track.artist_names,
                popularity=provider_track.popularity,
                release_year=provider_track.release_year,
                tempo=provider_track.tempo,
                energy=provider_track.energy,
                danceability=provider_track.danceability,
                acousticness=provider_track.acousticness,
                genres=provider_track.genres,
            )
            ranked_items.append(
                {
                    "track_id": track.id,
                    "rank": rank,
                    "confidence_score": item.confidence_score,
                    "explanation": item.explanation,
                }
            )

        return RecommendationResult(taste_profile=taste_profile, ranked_items=ranked_items)
