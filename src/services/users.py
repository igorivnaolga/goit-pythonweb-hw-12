from typing import Self
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.repository.users import UserRepository
from src.schemas.users import UserCreate


class UserService:
    def __init__(self: Self, db: AsyncSession):
        """
        Initialize the UserService with a database session.

        Args:
            db (AsyncSession): The async database session to be used for
            database operations.

        """
        self.repository = UserRepository(db)

    async def create_user(self: Self, body: UserCreate):
        """
        Create a new user.

        Args:
            body (UserCreate): The user details to create.

        Returns:
            User: The created user object.

        """
        avatar = None
        try:
            g = Gravatar(body.email)
            avatar = g.get_image()
        except Exception as e:
            print(e)
        return await self.repository.create_user(body, avatar)

    async def get_user_by_email(self: Self, email: str):
        """
        Retrieves a user by their email address.

        Args:
            email (str): The email address to search for.

        Returns:
            User: The user object associated with the provided email address, or None
            if no user is found.

        """
        return await self.repository.get_user_by_email(email)

    async def get_user_by_name(self: Self, username: str):
        """
        Retrieves a user by their username.

        Args:
            username (str): The username to search for.

        Returns:
            User or None: The user object associated with the provided username, or None
            if no user is found.

        """
        return await self.repository.get_user_by_name(username)

    async def confirmed_email(self: Self, email: str):
        """
        Confirms a user's email address.

        Args:
            email (str): The email address to confirm.

        Returns:
            None

        """
        return await self.repository.confirmed_email(email)

    async def update_avatar(self: Self, email: str, avatar_url: str):
        """
        Updates a user's avatar.

        Args:
            email (str): The email address associated with the user to update.
            avatar_url (str): The new avatar URL to use.

        Returns:
            None

        """
        return await self.repository.update_avatar(email, avatar_url)

    async def reset_password(self: Self, password: str, email: str):
        """
        Resets a user's password.

        Args:
            password (str): The new password to use.
            email (str): The email address associated with the user to update.

        Returns:
            None

        """
        return await self.repository.reset_password(password, email)
