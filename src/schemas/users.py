from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional
from src.database.models import UserRole


class UserModel(BaseModel):
    id: int
    username: str
    password: str
    email: EmailStr
    avatar: Optional[str] = None
    role: UserRole
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: UserRole


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    avatar: Optional[str] = None
    role: UserRole

    model_config = ConfigDict(from_attributes=True)


class RequestEmail(BaseModel):
    email: EmailStr


class RefreshTokenResponse(BaseModel):
    refresh_token: str


class TokenModel(BaseModel):
    refresh_token: str
    access_token: str
    token_type: str = "bearer"


class ResetPassword(BaseModel):
    new_password: str = Field(..., min_length=6, max_length=12)
