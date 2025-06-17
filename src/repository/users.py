from typing import Self

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.schemas.users import UserCreate, UserResponse


class UserRepository:
    def __init__(self: Self, session: AsyncSession):
        self.db = session

    async def get_user_by_email(self: Self, user_email: str) -> User | None:
        stmt = select(User).where(User.email == user_email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_name(self: Self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(
        self: Self, body: UserCreate, avatar: str | None
    ) -> User | None:
        user = User(
            **body.model_dump(exclude_unset=True, exclude={"password"}),
            password=body.password,
            avatar=avatar,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def confirmed_email(self: Self, user_email: str) -> None:
        user = await self.get_user_by_email(user_email)
        user.confirmed_email = True
        await self.db.commit()

    async def update_avatar(self: Self, email: str, url: str) -> UserResponse:
        user = await self.get_user_by_email(email)
        user.avatar = url
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def reset_password(self: Self, password: str, email: str) -> UserResponse:
        user = await self.get_user_by_email(email)
        user.password = password
        await self.db.commit()
        await self.db.refresh(user)
