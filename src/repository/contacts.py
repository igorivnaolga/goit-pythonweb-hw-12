from typing import List, Self, Optional
from datetime import datetime, timedelta

from sqlalchemy import select, delete, extract, or_, and_
from sqlalchemy.sql import extract
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Contact, User
from src.schemas.contacts import ContactBase, ContactUpdate


class ContactRepository:
    def __init__(self: Self, session: AsyncSession):
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
        stmt = select(Contact).filter(
            Contact.user_id == user.id, Contact.id == contact_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_contact(
        self: Self, body: ContactBase, user: User
    ) -> Contact | None:
        contact = Contact(**body.model_dump(exclude_unset=True), user=user)
        exist_contact = await self.get_contact_by_email(contact.email, user)
        if exist_contact:
            return None

        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def delete_contact(self: Self, contact_id: int, user: User) -> None:
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
        today = datetime.now().date()
        end_date = today + timedelta(days=7)

        stmt = (
            select(Contact)
            .where(
                Contact.user_id == user.id,
                or_(
                    # Дні народження в тому ж місяці
                    and_(
                        extract("month", Contact.birthday) == today.month,
                        extract("day", Contact.birthday) >= today.day,
                    ),
                    # Дні народження в наступному місяці (в межах 7 днів)
                    and_(
                        extract("month", Contact.birthday) == end_date.month,
                        extract("day", Contact.birthday) <= end_date.day,
                    ),
                    # Якщо сьогодні грудень, а кінець діапазону — січень
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
        stmt = select(Contact).filter(
            Contact.user_id == user.id, Contact.email == contact_email
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
