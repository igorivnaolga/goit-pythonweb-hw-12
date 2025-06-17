from typing import Self
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.repository.users import UserRepository
from src.schemas.users import UserCreate


class UserService:
    def __init__(self: Self, db: AsyncSession):
        self.repository = UserRepository(db)

    async def create_user(self: Self, body: UserCreate):
        avatar = None
        try:
            g = Gravatar(body.email)
            avatar = g.get_image()
        except Exception as e:
            print(e)
        return await self.repository.create_user(body, avatar)

    async def get_user_by_email(self: Self, email: str):
        return await self.repository.get_user_by_email(email)

    async def get_user_by_name(self: Self, username: str):
        return await self.repository.get_user_by_name(username)

    async def confirmed_email(self: Self, email: str):
        return await self.repository.confirmed_email(email)

    async def update_avatar(self: Self, email: str, avatar_url: str):
        return await self.repository.update_avatar(email, avatar_url)

    async def reset_password(self: Self, password: str, email: str):
        return await self.repository.reset_password(password, email)
