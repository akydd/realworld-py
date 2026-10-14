import jwt
from app.schemas.user import UserRegistrationRequest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.users import User
from app.schemas.user import UserResponse, UserResponseInner
from pwdlib import PasswordHash

ALGORITHM = "HS256"


class UserService:
    def __init__(self, db: AsyncSession, jwt_secret: str):
        self.db = db
        self.jwt_secret = jwt_secret
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
        await self.db.commit()
        await self.db.refresh(new_user)

        # create token
        jwt_token = jwt.encode(
            {"id": new_user.id}, self.jwt_secret, algorithm=ALGORITHM
        )

        return UserResponse(
            user=UserResponseInner(
                email=new_user.email,
                username=new_user.username,
                token=jwt_token,
                image=new_user.image,
                bio=new_user.bio,
            )
        )
