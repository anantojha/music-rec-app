"""Application-level exceptions, mapped to HTTP responses in app/main.py."""


class AppError(Exception):
    """Base class for all expected/handled application errors."""

    status_code = 400

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NotFoundError(AppError):
    status_code = 404


class UnauthorizedError(AppError):
    status_code = 401


class ForbiddenError(AppError):
    status_code = 403


class ConflictError(AppError):
    status_code = 409


class UpstreamServiceError(AppError):
    """Raised when a downstream API (Spotify, Apple Music, OpenAI) fails or times out."""

    status_code = 502
