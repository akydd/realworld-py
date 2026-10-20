from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.users import User
from app.schemas.user import (
    UserResponse,
    UserResponseInner,
    UserLoginRequest,
    UserRegistrationRequest,
)
from pwdlib import PasswordHash
from app.services.custom_errors import AuthenticationException
from app.services.auth import AuthService


class UserService:
    def __init__(self, db: AsyncSession, auth_service: AuthService):
        self.db = db
        self.auth_service = auth_service
        self.password_hash = PasswordHash.recommended()

    async def register_user(
        self, user_registration: UserRegistrationRequest
    ) -> UserResponse:
        user_data = user_registration.user.model_dump(
            exclude={"password"}, exclude_unset=True
        )
        hashed_password = self.password_hash.hash(user_registration.user.password)

        new_user: User = User(**user_data, password=hashed_password)
        self.db.add(new_user)
        await self.db.flush()
        await self.db.refresh(new_user)

        # create token
        jwt_token = self.auth_service.create_jwt_token(new_user.id)

        return self._db_user_to_model(new_user, jwt_token)

    async def login_user(self, user_login: UserLoginRequest) -> UserResponse:
        query = select(User).where(User.email == user_login.user.email)
        result = await self.db.execute(query)

        user = result.scalar_one_or_none()

        if not user or not self.password_hash.verify(
            user_login.user.password, user.password
        ):
            raise AuthenticationException()

        # create token
        jwt_token = self.auth_service.create_jwt_token(user.id)

        return self._db_user_to_model(user, jwt_token)

    def _db_user_to_model(self, db_user: User, token: str) -> UserResponse:
        return UserResponse(
            user=UserResponseInner(
                email=db_user.email,
                username=db_user.username,
                token=token,
                image=db_user.image,
                bio=db_user.bio,
            )
        )

    async def get_user(self, user_id: str) -> UserResponse:
        user: User = await self.db.get_one(User, user_id)

        if not user:
            raise AuthenticationException

        token = self.auth_service.create_jwt_token(user.id)
        return self._db_user_to_model(user, token)
