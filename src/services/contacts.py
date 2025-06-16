from sqlalchemy.ext.asyncio import AsyncSession
from typing import Self

from src.repository.contacts import ContactRepository
from src.schemas.contacts import ContactBase, ContactUpdate
from src.database.models import User


class ContactService:
    def __init__(self: Self, db: AsyncSession):
        self.repository = ContactRepository(db)

    async def create_contact(self: Self, body: ContactBase, user: User):
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
        return await self.repository.get_contacts(
            skip, limit, name, surname, email, user
        )

    async def get_contact(self: Self, contact_id: int, user: User):
        return await self.repository.get_contact(contact_id, user)

    async def update_contact(
        self: Self, contact_id: int, body: ContactUpdate, user: User
    ):
        return await self.repository.update_contact(contact_id, body, user)

    async def delete_contact(self: Self, contact_id: int, user: User):
        return await self.repository.delete_contact(contact_id, user)

    async def birthdays(self: Self, skip: int, limit: int, user: User):
        return await self.repository.get_birthdays(skip, limit, user)
