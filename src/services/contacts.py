from sqlalchemy.ext.asyncio import AsyncSession
from typing import Self

from src.repository.contacts import ContactRepository
from src.schemas.contacts import ContactBase, ContactUpdate
from src.database.models import User


class ContactService:
    def __init__(self: Self, db: AsyncSession):
        """
        Initialize the ContactService with a database session.

        Args:
            db (AsyncSession): The async database session to be used for
            database operations.

        """
        self.repository = ContactRepository(db)

    async def create_contact(self: Self, body: ContactBase, user: User):
        """
        Create a new contact for the specified user.

        Args:
            body (ContactBase): The contact details to create.
            user (User): The user for whom the contact is being created.

        Returns:
            Contact or None: The created contact object, or None if a contact
            with the same email already exists.

        """
        return await self.repository.create_contact(body, user)

    async def get_contacts(
        self: Self,
        skip: int,
        limit: int,
        name: str | None,
        surname: str | None,
        email: str | None,
        user: User,
    ):
        """
        Get a list of contacts filtered by the specified criteria.

        Args:
            skip (int): The number of records to skip.
            limit (int): The maximum number of records to return.
            name (str | None): The name to filter by.
            surname (str | None): The surname to filter by.
            email (str | None): The email to filter by.
            user (User): The user for whom the contacts are being retrieved.

        Returns:
            List[Contact]: A list of contact objects that match the specified criteria.

        """
        return await self.repository.get_contacts(
            skip, limit, name, surname, email, user
        )

    async def get_contact(self: Self, contact_id: int, user: User):
        """
        Get a contact by id.

        Args:
            contact_id (int): The contact id.
            user (User): The user for whom the contact is being retrieved.

        Returns:
            Contact | None: The contact object with the specified id, or None if it does not exist.

        """
        return await self.repository.get_contact(contact_id, user)

    async def update_contact(
        self: Self, contact_id: int, body: ContactUpdate, user: User
    ):
        """
        Update a contact by id.

        Args:
            contact_id (int): The id of the contact to update.
            body (ContactUpdate): The details of the contact to update.
            user (User): The user performing the update.

        Returns:
            Contact | None: The updated contact object, or None if the contact does not exist.

        """
        return await self.repository.update_contact(contact_id, body, user)

    async def delete_contact(self: Self, contact_id: int, user: User):
        """
        Delete a contact by id.

        Args:
            contact_id (int): The id of the contact to delete.
            user (User): The user performing the deletion.

        Returns:
            None

        """
        return await self.repository.delete_contact(contact_id, user)

    async def birthdays(self: Self, skip: int, limit: int, user: User):
        """
        Retrieve a list of contacts with upcoming birthdays.

        Args:
            skip (int): The number of records to skip.
            limit (int): The maximum number of records to return.
            user (User): The user for whom the birthdays are being retrieved.

        Returns:
            List[Contact]: A list of contact objects with birthdays within the upcoming week.

        """
        return await self.repository.get_birthdays(skip, limit, user)
