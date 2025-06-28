from datetime import datetime
from uuid import UUID

from factory.alchemy import SQLAlchemyModelFactory
from factory.declarations import LazyFunction
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User, UserRole, Contact

fake = Faker()


class BaseFactory(SQLAlchemyModelFactory):
    @classmethod
    def build_dict(cls, **kwargs) -> dict:
        data = {}
        for key, value in cls.build(**kwargs).__dict__.items():
            if key == "_sa_instance_state":
                continue
            if isinstance(value, UUID):
                data[key] = str(value)
            else:
                data[key] = value
        return data

    @classmethod
    async def create_(cls, db: AsyncSession, **kwargs):
        cls._meta.sqlalchemy_session = db

        fields = cls.build_dict(**kwargs)
        for key, value in fields.items():
            if isinstance(value, datetime):
                fields[key] = value.replace(tzinfo=None)
        obj = cls._meta.model(**fields)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj


class UserFactory(BaseFactory):
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = User

    username = LazyFunction(lambda: fake.user_name())
    email = LazyFunction(lambda: fake.email())
    password = LazyFunction(lambda: fake.password())
    role = UserRole.USER
    avatar = "https://example.com/avatar.jpg"


class ContactsFactory(BaseFactory):
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = Contact

    first_name = LazyFunction(lambda: fake.first_name())
    last_name = LazyFunction(lambda: fake.last_name())
    email = LazyFunction(lambda: fake.email())
    phone = LazyFunction(lambda: fake.phone_number()[:12])
    birthday = LazyFunction(lambda: fake.date_of_birth())
    info = LazyFunction(lambda: fake.text())
