from fastapi import APIRouter, Depends
from app.schemas.user import UserRegistrationRequest, UserResponse
from app.core.config import Settings, get_settings
from app.db.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user import UserService

router = APIRouter(prefix="/api/users", tags=["users"])


def get_user_service(
    settings: Settings = Depends(get_settings), db: AsyncSession = Depends(get_db)
) -> UserService:
    return UserService(db=db, jwt_secret=settings.jwt_secret)


@router.post("")
async def register_user(
    user_registration: UserRegistrationRequest,
    users_service: UserService = Depends(get_user_service),
) -> UserResponse:
    return await users_service.register_user(user_registration)
