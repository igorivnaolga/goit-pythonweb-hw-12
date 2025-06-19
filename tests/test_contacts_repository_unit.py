import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from src.repository.contacts import ContactRepository
from src.database.models import User, Contact
from src.schemas.contacts import ContactBase


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def contact_repository(mock_session):
    return ContactRepository(mock_session)


@pytest.fixture
def user():
    return User(
        id=1,
        username="bobfeta",
        email="bob.feta@example.com",
        password="securepassword",
        confirmed_email=True,
        avatar="https://example.com/avatar.jpg",
        role="USER",
    )


@pytest.mark.asyncio
async def test_create_contact(contact_repository, mock_session, user):
    contact_data = ContactBase(
        first_name="Bob",
        last_name="Feta",
        email="bob.feta@example.com",
        phone="+1234567890",
        birthday="1990-01-01",
        info="Test contact",
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await contact_repository.create_contact(contact_data, user)

    assert isinstance(result, Contact)
    assert result.first_name == "Bob"
    assert result.last_name == "Feta"
    assert result.email == "bob.feta@example.com"
    assert result.phone == "+1234567890"
    assert result.birthday == datetime(1990, 1, 1).date()
    assert result.info == "Test contact"


@pytest.mark.asyncio
async def test_create_contact_already_exists(contact_repository, mock_session, user):
    contact_data = ContactBase(
        first_name="Bob",
        last_name="Feta",
        email="bob.feta@example.com",
        phone="+1234567890",
        birthday="1990-01-01",
        info="Test contact",
    )
    existing_contact = Contact(**contact_data.model_dump(), user_id=user.id)

    contact_repository.get_contact_by_email = AsyncMock(return_value=existing_contact)

    result = await contact_repository.create_contact(contact_data, user)

    assert result is None
    contact_repository.get_contact_by_email.assert_awaited_once_with(
        "bob.feta@example.com", user
    )


@pytest.mark.asyncio
async def test_get_contacts(contact_repository, mock_session, user):
    contact_list = [
        Contact(
            first_name="Bob",
            last_name="Feta",
            email="bob.feta@example.com",
            phone="+1234567890",
            birthday=datetime(1990, 1, 1),
            info="Friend",
            user_id=user.id,
        )
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = contact_list
    mock_session.execute = AsyncMock(return_value=mock_result)

    contacts = await contact_repository.get_contacts(0, 10, None, None, None, user)

    assert len(contacts) == 1
    assert contacts[0].first_name == "Bob"
    assert contacts[0].email == "bob.feta@example.com"


@pytest.mark.asyncio
async def test_get_contact_by_email(contact_repository, mock_session, user):
    contact = Contact(
        first_name="Bob",
        last_name="Feta",
        email="bob.feta@example.com",
        phone="+1234567890",
        birthday=datetime(1990, 1, 1),
        info="Friend",
        user_id=user.id,
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = contact
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await contact_repository.get_contact_by_email("bob.feta@example.com", user)

    assert result.first_name == "Bob"
    assert result.email == "bob.feta@example.com"


@pytest.mark.asyncio
async def test_get_contact(contact_repository, mock_session, user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = ContactBase(
        first_name="Bob",
        last_name="Feta",
        email="bob.feta@example.com",
        phone="+1234567890",
        birthday="1990-01-01",
        info="Test contact",
    )
    mock_session.execute = AsyncMock(return_value=mock_result)

    contact = await contact_repository.get_contact(1, user)

    assert contact.first_name == "Bob"
    assert contact.last_name == "Feta"
    assert contact.email == "bob.feta@example.com"
    assert contact.phone == "+1234567890"
    assert contact.birthday == datetime(1990, 1, 1).date()
    assert contact.info == "Test contact"
    assert mock_session.execute.call_count == 1


@pytest.mark.asyncio
async def test_update_contact(contact_repository, mock_session, user):
    existing_contact = Contact(id=1, user_id=1, first_name="Bob", last_name="Feta")

    contact_data = ContactBase(
        first_name="Bobby",
        last_name="Feta",
        email="bobby.feta@example.com",
        phone="+1234567890",
        birthday="1990-01-01",
        info="Updated contact",
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_contact
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await contact_repository.update_contact(1, contact_data, user)

    assert result is not None
    assert existing_contact.first_name == "Bobby"
    assert existing_contact.last_name == "Feta"
    assert existing_contact.info == "Updated contact"
    assert mock_session.execute.call_count == 1
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_contact(contact_repository, mock_session, user):
    contact = Contact(
        id=1,
        user_id=user.id,
        first_name="Bob",
        last_name="Feta",
        email="bob.feta@example.com",
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = contact
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await contact_repository.delete_contact(1, user)

    assert result is True
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_birthdays(contact_repository, mock_session, user):
    contact = Contact(
        first_name="Bob",
        last_name="Feta",
        email="bob.feta@example.com",
        birthday=datetime(1990, 1, 1),
        user_id=user.id,
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [contact]
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await contact_repository.get_birthdays(0, 10, user)

    assert len(result) == 1
    assert result[0].first_name == "Bob"
