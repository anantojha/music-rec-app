import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.api import apple_music, auth, recommendations, spotify, users
from app.core.config import settings
from app.core.exceptions import AppError

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="AI Music Recommender API",
    description="Analyzes a Spotify playlist and returns GPT-ranked song recommendations.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_base_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic per-IP rate limiting. In production this is complemented by AWS WAF /
# ALB rate-based rules in front of the service (see terraform/alb.tf).
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Used by the ALB target group health check."""
    return {"status": "ok", "environment": settings.environment}


app.include_router(auth.router)
app.include_router(spotify.router)
app.include_router(apple_music.router)
app.include_router(recommendations.router)
app.include_router(users.router)
