from datetime import datetime
from uuid import UUID

from factory.base import StubFactory
from factory.declarations import LazyFunction
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User, UserRole

fake = Faker()


class BaseFactory(StubFactory):
    @classmethod
    def build_dict(cls, **kwargs) -> dict:
        """Build a model dict from kwargs."""
        data = {}
        for key, value in cls.build(**kwargs).__dict__.items():
            # Remove
            if key == "_sa_instance_state":
                continue
            # Convert UUID -> str
            if isinstance(value, UUID):
                data[key] = str(value)
            else:
                data[key] = value
        return data

    @classmethod
    async def create_(  # noqa: ANN206
        cls,
        db: AsyncSession,
        **kwargs,
    ):
        """Async version of create method."""
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
