from typing import List, Self, Optional
from datetime import datetime, timedelta

from sqlalchemy import select, delete, extract, or_, and_
from sqlalchemy.sql import extract
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Contact, User
from src.schemas.contacts import ContactBase, ContactUpdate


class ContactRepository:
    def __init__(self: Self, session: AsyncSession):
        """
        Initialize the ContactRepository with a database session.

        Args:
            session (AsyncSession): The async database session to be used for
            database operations.

        """
        self.db = session

    async def get_contacts(
        self: Self,
        skip: int,
        limit: int,
        name: str | None,
        surname: str | None,
        email: str | None,
        user: User,
    ) -> List[Contact]:
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
        stmt = select(Contact).filter(Contact.user_id == user.id)
        if name:
            stmt = stmt.filter(first_name=name)
        if surname:
            stmt = stmt.filter(last_name=surname)
        if email:
            stmt = stmt.filter(email=email)
        stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_contact(self: Self, contact_id: int, user: User) -> Contact | None:
        """
        Get a contact by id.

        Args:
            contact_id (int): The id of the contact to retrieve.
            user (User): The user for whom the contact is being retrieved.

        Returns:
            Contact | None: The contact object with the specified id, or None if it does not exist.

        """
        stmt = select(Contact).filter(
            Contact.user_id == user.id, Contact.id == contact_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_contact(
        self: Self, body: ContactBase, user: User
    ) -> Contact | None:
        """
        Create a new contact for the specified user.

        Args:
            body (ContactBase): The contact details to create.
            user (User): The user for whom the contact is being created.

        Returns:
            Contact | None: The created contact object, or None if a contact
            with the same email already exists.

        """
        contact = Contact(**body.model_dump(exclude_unset=True), user=user)
        exist_contact = await self.get_contact_by_email(contact.email, user)
        if exist_contact:
            return None

        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def delete_contact(self: Self, contact_id: int, user: User) -> None:
        """
        Delete a contact by id.

        Args:
            contact_id (int): The id of the contact to delete.
            user (User): The user performing the deletion.

        Returns:
            None: Returns None if the contact does not exist, otherwise True after successful deletion.

        """
        contact = await self.get_contact(contact_id, user)
        if contact is None:
            return None
        stmt = delete(Contact).where(Contact.id == contact_id)
        await self.db.execute(stmt)
        await self.db.commit()
        return True

    async def update_contact(
        self: Self, contact_id: int, body: ContactUpdate, user: User
    ) -> Contact | None:
        """
        Update a contact by id.

        Args:
            contact_id (int): The id of the contact to update.
            body (ContactUpdate): The details of the contact to update.
            user (User): The user performing the update.

        Returns:
            Contact | None: The updated contact object if it exists, otherwise None.

        """
        contact = await self.get_contact(contact_id, user)
        if contact:
            for key, value in body.model_dump(exclude_unset=True).items():
                setattr(contact, key, value)
            await self.db.commit()
            await self.db.refresh(contact)
        return contact

    async def get_birthdays(
        self: Self, skip: int, limit: int, user: User
    ) -> List[Contact]:
        """
        Get a list of contacts with upcoming birthdays.

        Args:
            skip (int): The number of records to skip.
            limit (int): The maximum number of records to return.
            user (User): The user for whom the birthdays are being retrieved.

        Returns:
            List[Contact]: A list of contact objects with birthdays within the upcoming week.

        """
        today = datetime.now().date()
        end_date = today + timedelta(days=7)

        stmt = (
            select(Contact)
            .where(
                Contact.user_id == user.id,
                or_(
                    # Birthdays in the same month
                    and_(
                        extract("month", Contact.birthday) == today.month,
                        extract("day", Contact.birthday) >= today.day,
                    ),
                    # Birthdays next month(in 7 days)
                    and_(
                        extract("month", Contact.birthday) == end_date.month,
                        extract("day", Contact.birthday) <= end_date.day,
                    ),
                    # If it is December and diapason ends in January
                    and_(
                        today.month == 12,
                        extract("month", Contact.birthday) == 1,
                        extract("day", Contact.birthday) <= end_date.day,
                    ),
                ),
            )
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_contact_by_email(
        self: Self, contact_email: str, user: User
    ) -> Contact | None:
        """
        Get a contact by email.

        Args:
            contact_email (str): The email to find the contact by.
            user (User): The user for whom the contact is being retrieved.

        Returns:
            Contact | None: The contact object with the specified email, or None if it does not exist.

        """
        stmt = select(Contact).filter(
            Contact.user_id == user.id, Contact.email == contact_email
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
