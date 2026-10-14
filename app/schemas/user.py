from pydantic import (
    BaseModel,
    StringConstraints,
    EmailStr,
    SecretStr,
    Field,
    ConfigDict,
)
from typing import Annotated

NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class UserRegistrationRequestInner(BaseModel):
    email: EmailStr
    username: NonEmptyString
    password: SecretStr = Field(..., min_length=8)


class UserRegistrationRequest(BaseModel):
    user: UserRegistrationRequestInner


class UserResponseInner(BaseModel):
    email: EmailStr
    token: NonEmptyString
    username: NonEmptyString
    bio: str | None = None
    image: str | None = None
    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    user: UserResponseInner
    model_config = ConfigDict(from_attributes=True)
