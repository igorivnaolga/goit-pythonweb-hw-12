from typing import Self

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.schemas.users import UserCreate, UserResponse


class UserRepository:
    def __init__(self: Self, session: AsyncSession):
        """
        Initialize the UserRepository with a database session.

        Args:
            session (AsyncSession): The async database session to be used for
            database operations.

        """
        self.db = session

    async def get_user_by_email(self: Self, user_email: str) -> User | None:
        """
        Retrieves a user by their email address.

        Args:
            user_email (str): The email address to search for.

        Returns:
            User | None: The user object associated with the provided email address, or None
            if no user is found.

        """
        stmt = select(User).where(User.email == user_email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_name(self: Self, username: str) -> User | None:
        """
        Retrieves a user by their username.

        Args:
            username (str): The username to search for.

        Returns:
            User | None: The user object associated with the provided username, or None
            if no user is found.

        """
        stmt = select(User).where(User.username == username)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(
        self: Self, body: UserCreate, avatar: str | None
    ) -> User | None:
        """
        Creates a new user.

        Args:
            body (UserCreate): The user details to create.
            avatar (str | None): The avatar URL to associate with the user.

        Returns:
            User | None: The created user object, or None if a user with the same email or username already exists.

        """
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
        """
        Confirms a user's email address.

        Args:
            user_email (str): The email address to confirm.

        Returns:
            None

        """
        user = await self.get_user_by_email(user_email)
        user.confirmed_email = True
        await self.db.commit()

    async def update_avatar(self: Self, email: str, url: str) -> UserResponse:
        """
        Updates a user's avatar.

        Args:
            email (str): The email address associated with the user to update.
            url (str): The new avatar URL to use.

        Returns:
            UserResponse: The updated user object.

        """
        user = await self.get_user_by_email(email)
        user.avatar = url
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def reset_password(self: Self, password: str, email: str) -> UserResponse:
        """
        Resets a user's password.

        Args:
            password (str): The new hashed password to set for the user.
            email (str): The email address associated with the user whose password is to be reset.

        Returns:
            UserResponse: The updated user object reflecting the new password.

        """
        user = await self.get_user_by_email(email)
        user.password = password
        await self.db.commit()
        await self.db.refresh(user)
