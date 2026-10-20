from fastapi import APIRouter, Depends
from app.schemas.user import UserRegistrationRequest, UserResponse, UserLoginRequest

from app.db.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user import UserService
from app.services.auth import AuthService
from app.core.config import Settings, get_settings

router = APIRouter(prefix="/api/users", tags=["users"])


def get_auth_service(settings: Settings = Depends(get_settings)) -> AuthService:
    return AuthService(jwt_secret=settings.jwt_secret)


def get_user_service(
    auth_service: AuthService = Depends(get_auth_service),
    db: AsyncSession = Depends(get_db),
) -> UserService:
    return UserService(db=db, auth_service=auth_service)


@router.post("")
async def register_user(
    user_registration: UserRegistrationRequest,
    users_service: UserService = Depends(get_user_service),
) -> UserResponse:
    return await users_service.register_user(user_registration)


@router.post("/login")
async def login_user(
    user_login: UserLoginRequest,
    users_service: UserService = Depends(get_user_service),
) -> UserResponse:
    return await users_service.login_user(user_login)
