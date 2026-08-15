"""
Repository pattern: keeps SQLAlchemy query construction out of the API layer and
service layer, making both easier to unit test (repositories can be mocked, or
tested against an in-memory/test Postgres independently of HTTP concerns).
"""
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.oauth_account import MusicProvider, OAuthAccount
from app.models.playlist import Playlist, PlaylistTrack
from app.models.recommendation import RecommendationHistory, RecommendationItem
from app.models.track import Track
from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, *, email: str, display_name: str, hashed_password: str | None) -> User:
        user = User(email=email, display_name=display_name, hashed_password=hashed_password)
        self.session.add(user)
        await self.session.flush()
        return user


class OAuthAccountRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_for_user(self, user_id: uuid.UUID, provider: MusicProvider) -> OAuthAccount | None:
        result = await self.session.execute(
            select(OAuthAccount).where(
                OAuthAccount.user_id == user_id, OAuthAccount.provider == provider
            )
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        *,
        user_id: uuid.UUID,
        provider: MusicProvider,
        provider_user_id: str,
        encrypted_access_token: str,
        encrypted_refresh_token: str | None,
        token_expires_at: datetime | None,
    ) -> OAuthAccount:
        existing = await self.get_for_user(user_id, provider)
        if existing:
            existing.provider_user_id = provider_user_id
            existing.encrypted_access_token = encrypted_access_token
            existing.encrypted_refresh_token = encrypted_refresh_token
            existing.token_expires_at = token_expires_at
            await self.session.flush()
            return existing

        account = OAuthAccount(
            user_id=user_id,
            provider=provider,
            provider_user_id=provider_user_id,
            encrypted_access_token=encrypted_access_token,
            encrypted_refresh_token=encrypted_refresh_token,
            token_expires_at=token_expires_at,
        )
        self.session.add(account)
        await self.session.flush()
        return account


class PlaylistRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_with_tracks(self, playlist_id: uuid.UUID) -> Playlist | None:
        result = await self.session.execute(
            select(Playlist)
            .where(Playlist.id == playlist_id)
            .options(selectinload(Playlist.track_links).selectinload(PlaylistTrack.track))
        )
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: uuid.UUID) -> list[Playlist]:
        result = await self.session.execute(select(Playlist).where(Playlist.user_id == user_id))
        return list(result.scalars().all())

    async def upsert_from_provider(
        self, *, user_id: uuid.UUID, provider: str, provider_playlist_id: str, name: str
    ) -> Playlist:
        result = await self.session.execute(
            select(Playlist).where(
                Playlist.user_id == user_id,
                Playlist.provider == provider,
                Playlist.provider_playlist_id == provider_playlist_id,
            )
        )
        playlist = result.scalar_one_or_none()
        if playlist:
            playlist.name = name
            await self.session.flush()
            return playlist

        playlist = Playlist(
            user_id=user_id, provider=provider, provider_playlist_id=provider_playlist_id, name=name
        )
        self.session.add(playlist)
        await self.session.flush()
        return playlist

    async def set_tracks(self, playlist: Playlist, tracks: list[Track]) -> None:
        """Replace a playlist's track list, preserving order via `position`."""
        playlist.track_links.clear()
        await self.session.flush()
        for position, track in enumerate(tracks):
            self.session.add(
                PlaylistTrack(playlist_id=playlist.id, track_id=track.id, position=position)
            )
        await self.session.flush()


class TrackRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_from_provider(self, *, provider: str, provider_track_id: str, **fields) -> Track:
        result = await self.session.execute(
            select(Track).where(
                Track.provider == provider, Track.provider_track_id == provider_track_id
            )
        )
        track = result.scalar_one_or_none()
        if track:
            for key, value in fields.items():
                setattr(track, key, value)
            await self.session.flush()
            return track

        track = Track(provider=provider, provider_track_id=provider_track_id, **fields)
        self.session.add(track)
        await self.session.flush()
        return track


class RecommendationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        source_playlist_id: uuid.UUID,
        taste_profile: dict,
        ranked_items: list[dict],
    ) -> RecommendationHistory:
        recommendation = RecommendationHistory(
            user_id=user_id, source_playlist_id=source_playlist_id, taste_profile=taste_profile
        )
        self.session.add(recommendation)
        await self.session.flush()

        for item in ranked_items:
            self.session.add(
                RecommendationItem(
                    recommendation_id=recommendation.id,
                    track_id=item["track_id"],
                    rank=item["rank"],
                    confidence_score=item["confidence_score"],
                    explanation=item["explanation"],
                )
            )
        await self.session.flush()
        return recommendation

    async def list_for_user(self, user_id: uuid.UUID) -> list[RecommendationHistory]:
        result = await self.session.execute(
            select(RecommendationHistory)
            .where(RecommendationHistory.user_id == user_id)
            .options(selectinload(RecommendationHistory.items))
            .order_by(RecommendationHistory.created_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, recommendation_id: uuid.UUID) -> RecommendationHistory | None:
        result = await self.session.execute(
            select(RecommendationHistory)
            .where(RecommendationHistory.id == recommendation_id)
            .options(selectinload(RecommendationHistory.items))
        )
        return result.scalar_one_or_none()

    async def delete(self, recommendation: RecommendationHistory) -> None:
        await self.session.delete(recommendation)
        await self.session.flush()
