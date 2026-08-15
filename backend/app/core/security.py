"""
Security primitives: password hashing, JWT issuance/verification, and symmetric
encryption for OAuth provider tokens at rest (per the security requirements in
the project spec: "OAuth tokens encrypted").
"""
from datetime import datetime, timedelta, timezone
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------
def hash_password(plain_password: str) -> str:
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _pwd_context.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------------
# JWT access tokens
# ---------------------------------------------------------------------------
ALGORITHM = "HS256"


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload: dict[str, Any] = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """Returns the subject (user id) encoded in the token, or None if invalid/expired."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


# ---------------------------------------------------------------------------
# Symmetric encryption for OAuth access/refresh tokens stored in Postgres
# ---------------------------------------------------------------------------
class TokenCipher:
    """Thin wrapper around Fernet so callers don't touch the crypto library directly."""

    def __init__(self, key: str):
        if not key:
            raise ValueError("TOKEN_ENCRYPTION_KEY must be set to store OAuth tokens securely.")
        self._fernet = Fernet(key.encode() if len(key) == 44 else Fernet.generate_key())

    def encrypt(self, raw: str) -> str:
        return self._fernet.encrypt(raw.encode()).decode()

    def decrypt(self, token: str) -> str:
        try:
            return self._fernet.decrypt(token.encode()).decode()
        except InvalidToken as exc:
            raise ValueError("Could not decrypt stored OAuth token.") from exc


def get_token_cipher() -> TokenCipher:
    return TokenCipher(settings.token_encryption_key)
