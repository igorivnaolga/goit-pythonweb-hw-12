from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional


class UserModel(BaseModel):
    id: int
    username: str
    password: str
    email: EmailStr
    avatar: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    avatar: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RequestEmail(BaseModel):
    email: EmailStr


class TokenModel(BaseModel):
    access_token: str
    token_type: str = "bearer"
