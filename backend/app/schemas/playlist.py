import uuid

from pydantic import BaseModel, ConfigDict


class TrackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    artist_names: list[str]
    provider_track_id: str


class PlaylistRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    provider: str
    provider_playlist_id: str


class PlaylistDetailRead(PlaylistRead):
    tracks: list[TrackRead] = []
