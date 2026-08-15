import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_openai_service, get_spotify_service
from app.core.exceptions import ForbiddenError, NotFoundError, UnauthorizedError
from app.core.security import get_token_cipher
from app.db.database import get_db
from app.db.repositories import (
    OAuthAccountRepository,
    PlaylistRepository,
    RecommendationRepository,
    TrackRepository,
)
from app.models.oauth_account import MusicProvider
from app.models.user import User
from app.schemas.recommendation import (
    GenerateRecommendationsRequest,
    LikeDislikeRequest,
    RecommendationHistoryRead,
)
from app.services.music_provider import ProviderTrack
from app.services.openai_service import OpenAIService
from app.services.recommendation_engine import RecommendationEngine
from app.services.spotify_service import SpotifyService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/generate", response_model=RecommendationHistoryRead)
async def generate_recommendations(
    payload: GenerateRecommendationsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    spotify: SpotifyService = Depends(get_spotify_service),
    openai_service: OpenAIService = Depends(get_openai_service),
) -> dict:
    playlist_repo = PlaylistRepository(db)
    track_repo = TrackRepository(db)
    recommendation_repo = RecommendationRepository(db)

    playlist = await playlist_repo.get_with_tracks(payload.playlist_id)
    if not playlist or playlist.user_id != current_user.id:
        raise NotFoundError("Playlist not found.")

    account = await OAuthAccountRepository(db).get_for_user(current_user.id, MusicProvider.SPOTIFY)
    if not account:
        raise UnauthorizedError("Connect a Spotify account before generating recommendations.")
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
        music_provider=spotify,
        openai_service=openai_service,
        playlist_repo=playlist_repo,
        track_repo=track_repo,
        recommendation_repo=recommendation_repo,
    )
    result = await engine.generate(access_token=access_token, playlist=playlist, source_tracks=source_tracks)

    recommendation = await recommendation_repo.create(
        user_id=current_user.id,
        source_playlist_id=playlist.id,
        taste_profile=result.taste_profile.model_dump(),
        ranked_items=result.ranked_items,
    )
    await db.commit()

    saved = await recommendation_repo.get(recommendation.id)
    return saved


@router.get("/history", response_model=list[RecommendationHistoryRead])
async def get_history(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list:
    return await RecommendationRepository(db).list_for_user(current_user.id)


@router.delete("/{recommendation_id}", status_code=204)
async def delete_recommendation(
    recommendation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    repo = RecommendationRepository(db)
    recommendation = await repo.get(recommendation_id)
    if not recommendation:
        raise NotFoundError("Recommendation not found.")
    if recommendation.user_id != current_user.id:
        raise ForbiddenError("You do not own this recommendation.")

    await repo.delete(recommendation)
    await db.commit()


@router.patch("/{recommendation_id}/items/{item_id}/feedback", status_code=204)
async def submit_feedback(
    recommendation_id: uuid.UUID,
    item_id: uuid.UUID,
    payload: LikeDislikeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Nice-to-have: like/dislike a single recommended song."""
    repo = RecommendationRepository(db)
    recommendation = await repo.get(recommendation_id)
    if not recommendation or recommendation.user_id != current_user.id:
        raise NotFoundError("Recommendation not found.")

    item = next((i for i in recommendation.items if i.id == item_id), None)
    if not item:
        raise NotFoundError("Recommendation item not found.")

    item.liked = payload.liked
    await db.commit()
