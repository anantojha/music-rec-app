"""
Thin wrapper around the OpenAI API for the two GPT calls in the recommendation
pipeline:
  - Step 2: build a structured taste profile from a playlist
  - Step 4: rank ~50 candidate songs down to the top 10 with explanations

Both calls request strict JSON output and validate it against a Pydantic schema,
so a malformed/hallucinated response raises immediately rather than propagating
bad data into the database.
"""
import json

from openai import AsyncOpenAI
from pydantic import BaseModel, Field, ValidationError

from app.core.config import settings
from app.core.exceptions import UpstreamServiceError
from app.schemas.recommendation import TasteProfile
from app.services.music_provider import ProviderTrack

TASTE_PROFILE_SYSTEM_PROMPT = """You are an expert music recommendation engine.
Analyze the given playlist and create a structured music taste profile.
Respond with ONLY valid JSON matching this exact shape, no prose, no markdown fences:
{
  "genres": [string],
  "mood": [string],
  "energy": "low" | "medium" | "high",
  "eras": [string],
  "recommended_search_terms": [string]
}"""

RANKING_SYSTEM_PROMPT = """You are an expert music recommendation engine.
Given a listener's taste profile and a list of candidate songs, select the best 10
songs for this listener. Respond with ONLY valid JSON, no prose, no markdown fences:
{
  "recommendations": [
    {"track_id": string, "confidence_score": number between 0 and 1, "explanation": string}
  ]
}
The "recommendations" array must contain exactly 10 items, ordered best-first,
and each "track_id" must be one of the candidate track_ids provided."""


class RankedTrack(BaseModel):
    track_id: str
    confidence_score: float = Field(ge=0, le=1)
    explanation: str


class RankingResult(BaseModel):
    recommendations: list[RankedTrack]


class OpenAIService:
    def __init__(self, client: AsyncOpenAI | None = None):
        self._client = client or AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model

    async def build_taste_profile(self, playlist_name: str, tracks: list[ProviderTrack]) -> TasteProfile:
        """Pipeline Step 2: turn a playlist into a structured taste profile."""
        track_lines = "\n".join(f"- {t.name} by {', '.join(t.artist_names)}" for t in tracks)
        user_prompt = f'Playlist: "{playlist_name}"\n\nTracks:\n{track_lines}'

        raw = await self._chat_json(TASTE_PROFILE_SYSTEM_PROMPT, user_prompt)
        try:
            return TasteProfile.model_validate(raw)
        except ValidationError as exc:
            raise UpstreamServiceError(f"GPT returned an invalid taste profile: {exc}") from exc

    async def rank_candidates(
        self, taste_profile: TasteProfile, candidates: list[ProviderTrack]
    ) -> list[RankedTrack]:
        """Pipeline Step 4: rank candidates and return the top 10 with explanations."""
        candidate_lines = "\n".join(
            f'- track_id="{c.provider_track_id}": {c.name} by {", ".join(c.artist_names)}'
            for c in candidates
        )
        user_prompt = (
            f"Taste profile:\n{taste_profile.model_dump_json(indent=2)}\n\n"
            f"Candidate songs:\n{candidate_lines}"
        )

        raw = await self._chat_json(RANKING_SYSTEM_PROMPT, user_prompt)
        try:
            result = RankingResult.model_validate(raw)
        except ValidationError as exc:
            raise UpstreamServiceError(f"GPT returned an invalid ranking response: {exc}") from exc

        valid_ids = {c.provider_track_id for c in candidates}
        filtered = [r for r in result.recommendations if r.track_id in valid_ids]
        return filtered[:10]

    async def _chat_json(self, system_prompt: str, user_prompt: str) -> dict:
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                temperature=0.4,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except Exception as exc:  # openai SDK raises several exception types
            raise UpstreamServiceError(f"OpenAI request failed: {exc}") from exc

        content = response.choices[0].message.content or "{}"
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise UpstreamServiceError(f"OpenAI returned non-JSON content: {content[:200]}") from exc
