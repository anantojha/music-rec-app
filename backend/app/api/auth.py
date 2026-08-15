from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.exceptions import UnauthorizedError
from app.core.security import create_access_token, verify_password
from app.db.database import get_db
from app.db.repositories import UserRepository
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    user = await UserRepository(db).get_by_email(payload.email)
    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise UnauthorizedError("Incorrect email or password.")

    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.post("/logout", status_code=204)
async def logout(current_user: User = Depends(get_current_user)) -> None:
    # JWTs are stateless; logout is enforced client-side by discarding the token.
    # If a revocation list is needed later, add the token's jti to a denylist here.
    return None
