from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.exceptions import ConflictError
from app.core.security import hash_password
from app.db.database import get_db
from app.db.repositories import OAuthAccountRepository, UserRepository
from app.models.oauth_account import MusicProvider
from app.models.user import User
from app.schemas.user import LinkedAccountRead, UserRead

router = APIRouter(prefix="/users", tags=["users"])


class RegisterRequest(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8)


@router.post("", response_model=UserRead, status_code=201)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> User:
    repo = UserRepository(db)
    if await repo.get_by_email(payload.email):
        raise ConflictError("An account with this email already exists.")

    user = await repo.create(
        email=payload.email,
        display_name=payload.display_name,
        hashed_password=hash_password(payload.password),
    )
    await db.commit()
    return user


@router.get("/me/linked-accounts", response_model=list[LinkedAccountRead])
async def linked_accounts(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list:
    repo = OAuthAccountRepository(db)
    accounts = []
    for provider in MusicProvider:
        account = await repo.get_for_user(current_user.id, provider)
        if account:
            accounts.append(account)
    return accounts
