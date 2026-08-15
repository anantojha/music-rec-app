# AI Music Recommender — Backend

A FastAPI service that connects to a user's Spotify account, analyzes a selected
playlist with GPT, and returns 10 ranked song recommendations with natural-language
explanations. Built as the backend half of a full-stack portfolio project
demonstrating production patterns: layered architecture, an abstraction layer for
swappable music providers, encrypted credential storage, and a fully mocked unit
test suite for every external dependency.

## Architecture

```
app/
├── api/                  # HTTP routing layer — thin, no business logic
│   ├── auth.py           # POST /auth/login, GET /auth/me, POST /auth/logout
│   ├── spotify.py        # OAuth connect/callback, playlist listing/detail
│   ├── apple_music.py    # placeholder — see "Provider abstraction" below
│   ├── recommendations.py# POST /recommendations/generate, history, delete, feedback
│   ├── users.py          # registration, linked accounts
│   └── deps.py           # shared FastAPI dependencies (current user, service factories)
├── services/
│   ├── music_provider.py       # abstract MusicProviderClient interface
│   ├── spotify_service.py      # Spotify implementation (OAuth, playlists, search)
│   ├── apple_music_service.py  # stub implementation, same interface
│   ├── openai_service.py       # GPT calls for taste profiling + candidate ranking
│   └── recommendation_engine.py# orchestrates the 4-step pipeline
├── models/                # SQLAlchemy 2.0 ORM models
├── schemas/                # Pydantic request/response + the TasteProfile contract
├── db/
│   ├── database.py         # async engine/session
│   └── repositories.py     # all DB queries — keeps queries out of routes/services
├── workers/
│   └── recommendation_worker.py  # background-job version of the pipeline
└── core/
    ├── config.py           # pydantic-settings, one Settings object
    ├── security.py         # JWT, password hashing, Fernet token encryption
    └── exceptions.py        # AppError hierarchy → HTTP status mapping
```

### Why a provider abstraction?

The spec calls for Spotify now and Apple Music later. Rather than hardcoding
Spotify calls into the recommendation engine, every provider implements
`MusicProviderClient` (`get_authorization_url`, `list_playlists`,
`get_playlist_tracks`, `search_candidates`, ...). `RecommendationEngine` and every
API route depend on that interface, never on `SpotifyService` directly. Adding
Apple Music later means finishing `AppleMusicService` and registering it — no
changes to the pipeline or routing layer.

### The recommendation pipeline

1. **Build playlist profile** — the connected provider returns tracks with cached
   audio features (tempo, energy, danceability, acousticness, popularity, genres).
2. **GPT taste profile** — `OpenAIService.build_taste_profile()` sends the playlist
   to GPT and parses the response into a strict `TasteProfile` Pydantic model
   (`genres`, `mood`, `energy`, `eras`, `recommended_search_terms`). Invalid/
   hallucinated JSON raises immediately instead of corrupting downstream state.
3. **Candidate retrieval** — `search_candidates()` fetches ~50 candidates from the
   provider using the profile's genres/search terms. Tracks already in the source
   playlist are filtered out before ranking.
4. **GPT ranking** — `OpenAIService.rank_candidates()` sends the profile + candidates
   back to GPT, which returns the top 10 with a confidence score and explanation
   each. Any track ID GPT hallucinates outside the candidate set is discarded.

## Data model

`users` · `oauth_accounts` (encrypted provider tokens) · `albums` · `tracks`
(cached audio features) · `playlists` · `playlist_track` (ordered join table) ·
`recommendation_history` (stores the taste profile JSON per run) ·
`recommendation_items` (rank, confidence score, explanation, like/dislike).

## Security

- OAuth access/refresh tokens are encrypted at rest with Fernet
  (`core/security.py::TokenCipher`) before being written to `oauth_accounts`.
- Authentication is stateless JWT (`python-jose`), bcrypt password hashing
  (`passlib`).
- Per-IP rate limiting via `slowapi`, intended to sit behind AWS WAF / ALB
  rate-based rules in production.
- All request/response bodies are validated with Pydantic.
- CORS is restricted to `FRONTEND_BASE_URL`.

## Running locally

```bash
cp .env.example .env        # fill in Spotify + OpenAI credentials
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Postgres must be running and reachable at DATABASE_URL
alembic upgrade head

uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs` once running.

## Testing

```bash
pip install -r requirements.txt
pytest -v
```

All external dependencies (OpenAI, Spotify's HTTP API) are mocked — tests never
require network access or a running database:

- `tests/test_security.py` — password hashing, JWT round-trip/expiry, token
  encryption round-trip.
- `tests/test_openai_service.py` — taste-profile JSON validation (including
  rejecting malformed GPT output), ranking response filtering (dropping
  hallucinated track IDs, capping at 10 results).
- `tests/test_recommendation_engine.py` — full 4-step pipeline orchestration,
  empty-playlist/no-candidates/no-valid-rankings error paths, verifying
  already-owned tracks are excluded from candidates before ranking.
- `tests/test_spotify_service.py` — OAuth token exchange, playlist listing,
  playlist track fetching with audio-feature merging, and graceful degradation
  when the audio-features endpoint fails.

> **Note:** this sandbox has no network access, so dependencies could not be
> `pip install`-ed and pytest could not be executed here. All files pass
> `python -m py_compile`. Run `pytest -v` locally to execute the suite before
> relying on it.

## API reference

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/login` | Email/password login → JWT |
| GET | `/auth/me` | Current user |
| POST | `/auth/logout` | No-op (stateless JWT) |
| POST | `/users` | Register a new account |
| GET | `/users/me/linked-accounts` | List connected music providers |
| GET | `/spotify/connect` | Get Spotify OAuth authorization URL |
| GET | `/spotify/callback` | OAuth redirect target, stores encrypted tokens |
| GET | `/spotify/playlists` | List + sync the user's Spotify playlists |
| GET | `/spotify/playlists/{id}` | Fetch + sync one playlist's tracks |
| POST | `/recommendations/generate` | Run the full 4-step pipeline for a playlist |
| GET | `/recommendations/history` | Past recommendation runs |
| DELETE | `/recommendations/{id}` | Delete a recommendation run |
| PATCH | `/recommendations/{id}/items/{item_id}/feedback` | Like/dislike a song |

## Database migrations

```bash
alembic upgrade head                          # apply migrations
alembic revision --autogenerate -m "message"  # generate a new migration
```

## Docker

```bash
docker build -t ai-music-recommender-backend .
docker run -p 8000:8000 --env-file .env ai-music-recommender-backend
```

Multi-stage build, runs as a non-root user, includes a container `HEALTHCHECK`
matching the `/health` endpoint the ALB target group polls in production.

## What's next

- Frontend (React + Vite + TypeScript)
- Terraform (`networking.tf`, `ecs.tf`, `rds.tf`, `alb.tf`, `iam.tf`, `secrets.tf`)
- Excalidraw diagrams (architecture, AWS infra, DB schema, recommendation
  pipeline, sequence flow, deployment pipeline)
- GitHub Actions CI/CD (test → lint → build → push to ECR → deploy ECS)
