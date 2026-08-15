import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TasteProfile(BaseModel):
    """
    The structured JSON contract GPT must return in pipeline Step 2.
    Keeping this as a strict Pydantic model means a malformed/hallucinated GPT
    response fails validation immediately instead of silently corrupting downstream
    candidate retrieval or ranking.
    """

    genres: list[str] = Field(default_factory=list)
    mood: list[str] = Field(default_factory=list)
    energy: Literal["low", "medium", "high"] = "medium"
    eras: list[str] = Field(default_factory=list)
    recommended_search_terms: list[str] = Field(default_factory=list)


class GenerateRecommendationsRequest(BaseModel):
    playlist_id: uuid.UUID


class RecommendationItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    track_id: uuid.UUID
    rank: int
    confidence_score: float
    explanation: str
    liked: bool | None = None


class RecommendationHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_playlist_id: uuid.UUID
    taste_profile: TasteProfile
    created_at: datetime
    items: list[RecommendationItemRead] = []


class LikeDislikeRequest(BaseModel):
    liked: bool
