"""
Background recommendation generation (nice-to-have from the spec).

The synchronous path (POST /recommendations/generate) calls RecommendationEngine
directly and blocks until GPT + Spotify calls finish, which is fine for an MVP but
can take several seconds. This worker wraps the same engine so it can be run:

  - via FastAPI's BackgroundTasks for a quick win (see usage note below), or
  - via a real task queue (SQS + a worker process, Celery, arq, etc.) in production,
    which is the more scalable option for ECS Fargate since it decouples the
    request/response cycle from slow LLM calls.

This module intentionally has no FastAPI/HTTP imports so it can run standalone
in a worker process/container, separate from the API service.
"""
import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import (
    OAuthAccountRepository,
    PlaylistRepository,
    RecommendationRepository,
    TrackRepository,
)
from app.models.oauth_account import MusicProvider
from app.core.security import get_token_cipher
from app.services.music_provider import ProviderTrack
from app.services.openai_service import OpenAIService
from app.services.recommendation_engine import RecommendationEngine
from app.services.spotify_service import SpotifyService

logger = logging.getLogger(__name__)


async def generate_recommendations_job(db: AsyncSession, *, user_id: uuid.UUID, playlist_id: uuid.UUID) -> None:
    """Runs the full recommendation pipeline and persists the result.
    Designed to be called with a request-scoped session from BackgroundTasks,
    or with a fresh session obtained by a standalone worker process."""
    playlist_repo = PlaylistRepository(db)
    track_repo = TrackRepository(db)
    recommendation_repo = RecommendationRepository(db)

    playlist = await playlist_repo.get_with_tracks(playlist_id)
    if not playlist or playlist.user_id != user_id:
        logger.warning("recommendation_worker: playlist %s not found for user %s", playlist_id, user_id)
        return

    account = await OAuthAccountRepository(db).get_for_user(user_id, MusicProvider.SPOTIFY)
    if not account:
        logger.warning("recommendation_worker: user %s has no connected Spotify account", user_id)
        return
    access_token = get_token_cipher().decrypt(account.encrypted_access_token)

    source_tracks = [
        ProviderTrack(
            provider_track_id=link.track.provider_track_id,
            name=link.track.name,
            artist_names=link.track.artist_names,
            release_year=link.track.release_year,
            popularity=link.track.popularity,
            tempo=link.track.tempo,
            energy=link.track.energy,
            danceability=link.track.danceability,
            acousticness=link.track.acousticness,
            genres=link.track.genres,
        )
        for link in playlist.track_links
    ]

    engine = RecommendationEngine(
        music_provider=SpotifyService(),
        openai_service=OpenAIService(),
        playlist_repo=playlist_repo,
        track_repo=track_repo,
        recommendation_repo=recommendation_repo,
    )

    try:
        result = await engine.generate(access_token=access_token, playlist=playlist, source_tracks=source_tracks)
    except Exception:
        logger.exception("recommendation_worker: pipeline failed for playlist %s", playlist_id)
        return

    await recommendation_repo.create(
        user_id=user_id,
        source_playlist_id=playlist.id,
        taste_profile=result.taste_profile.model_dump(),
        ranked_items=result.ranked_items,
    )
    await db.commit()
    logger.info("recommendation_worker: generated recommendations for playlist %s", playlist_id)
