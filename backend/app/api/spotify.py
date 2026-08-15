import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_spotify_service
from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.security import create_access_token, decode_access_token, get_token_cipher
from app.db.database import get_db
from app.db.repositories import OAuthAccountRepository, PlaylistRepository, TrackRepository
from app.models.oauth_account import MusicProvider
from app.models.user import User
from app.schemas.playlist import PlaylistDetailRead, PlaylistRead
from app.services.spotify_service import SpotifyService

router = APIRouter(prefix="/spotify", tags=["spotify"])


@router.get("/connect")
async def connect(
    current_user: User = Depends(get_current_user),
    spotify: SpotifyService = Depends(get_spotify_service),
) -> dict:
    """Returns the Spotify authorization URL for the frontend to redirect to.
    The current user's id is embedded (signed, short-lived) in `state` so the
    /callback redirect -- which Spotify calls with no Authorization header --
    can still identify who is connecting their account."""
    state = create_access_token(subject=str(current_user.id), expires_delta=timedelta(minutes=10))
    url = await spotify.get_authorization_url(state=state)
    return {"authorization_url": url}


@router.get("/callback")
async def callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
    spotify: SpotifyService = Depends(get_spotify_service),
) -> RedirectResponse:
    user_id_str = decode_access_token(state)
    if not user_id_str:
        raise UnauthorizedError("Invalid or expired Spotify OAuth state.")
    user_id = uuid.UUID(user_id_str)

    tokens = await spotify.exchange_code_for_tokens(code)
    cipher = get_token_cipher()
    expires_at = (
        datetime.now(timezone.utc) + timedelta(seconds=tokens["expires_in"])
        if tokens.get("expires_in")
        else None
    )

    await OAuthAccountRepository(db).upsert(
        user_id=user_id,
        provider=MusicProvider.SPOTIFY,
        provider_user_id=user_id_str,  # Spotify profile id isn't fetched here to keep the callback fast;
        # a background job or the next /spotify/playlists call can backfill it if needed.
        encrypted_access_token=cipher.encrypt(tokens["access_token"]),
        encrypted_refresh_token=cipher.encrypt(tokens["refresh_token"]) if tokens.get("refresh_token") else None,
        token_expires_at=expires_at,
    )
    await db.commit()

    return RedirectResponse(url=f"{settings.frontend_base_url}/dashboard?spotify_connected=true")


@router.get("/playlists", response_model=list[PlaylistRead])
async def get_playlists(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    spotify: SpotifyService = Depends(get_spotify_service),
) -> list:
    access_token = await _get_decrypted_access_token(db, current_user.id)
    provider_playlists = await spotify.list_playlists(access_token)

    playlist_repo = PlaylistRepository(db)
    saved = [
        await playlist_repo.upsert_from_provider(
            user_id=current_user.id,
            provider="spotify",
            provider_playlist_id=p.provider_playlist_id,
            name=p.name,
        )
        for p in provider_playlists
    ]
    await db.commit()
    return saved


@router.get("/playlists/{playlist_id}", response_model=PlaylistDetailRead)
async def get_playlist_detail(
    playlist_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    spotify: SpotifyService = Depends(get_spotify_service),
) -> dict:
    access_token = await _get_decrypted_access_token(db, current_user.id)

    playlist_repo = PlaylistRepository(db)
    track_repo = TrackRepository(db)

    provider_tracks = await spotify.get_playlist_tracks(access_token, playlist_id)
    playlist = await playlist_repo.upsert_from_provider(
        user_id=current_user.id, provider="spotify", provider_playlist_id=playlist_id, name=playlist_id
    )

    tracks = [
        await track_repo.get_or_create_from_provider(
            provider="spotify",
            provider_track_id=t.provider_track_id,
            name=t.name,
            artist_names=t.artist_names,
            popularity=t.popularity,
            release_year=t.release_year,
            tempo=t.tempo,
            energy=t.energy,
            danceability=t.danceability,
            acousticness=t.acousticness,
            genres=t.genres,
        )
        for t in provider_tracks
    ]
    await playlist_repo.set_tracks(playlist, tracks)
    await db.commit()

    return {
        "id": playlist.id,
        "name": playlist.name,
        "provider": playlist.provider,
        "provider_playlist_id": playlist.provider_playlist_id,
        "tracks": tracks,
    }


async def _get_decrypted_access_token(db: AsyncSession, user_id) -> str:
    account = await OAuthAccountRepository(db).get_for_user(user_id, MusicProvider.SPOTIFY)
    if not account:
        raise UnauthorizedError("No connected Spotify account for this user.")
    return get_token_cipher().decrypt(account.encrypted_access_token)
