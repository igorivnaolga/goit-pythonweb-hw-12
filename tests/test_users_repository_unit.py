import pytest
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession

from src.repository.users import UserRepository
from src.database.models import User, UserRole
from src.schemas.users import UserCreate


@pytest.fixture
def mock_session():
    mock_session = AsyncMock(spec=AsyncSession)
    return mock_session


@pytest.fixture
def user_repository(mock_session):
    return UserRepository(mock_session)


@pytest.fixture
def test_user():
    return User(
        id=1,
        username="testuser",
        email="test@test.com",
        password="testpassword",
        confirmed_email=True,
        avatar="https://example.com/avatar.jpg",
        role="USER",
    )


@pytest.mark.asyncio
async def test_get_user_by_email(user_repository, mock_session, test_user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = test_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repository.get_user_by_email("test@test.com")

    assert result is not None
    assert result.id == test_user.id
    assert result.username == test_user.username
    assert result.email == test_user.email


@pytest.mark.asyncio
async def test_get_user_by_name(user_repository, mock_session, test_user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = test_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repository.get_user_by_name("testuser")

    assert result is not None
    assert result.id == test_user.id
    assert result.username == test_user.username
    assert result.email == test_user.email


@pytest.mark.asyncio
async def test_create_user(user_repository, mock_session, test_user):
    user_data = UserCreate(
        username="testuser",
        email="test@test.com",
        password="testpassword",
        role=UserRole.USER,
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repository.create_user(
        user_data, "https://example.com/avatar.jpg"
    )

    assert result is not None
    assert result.username == user_data.username
    assert result.email == user_data.email


@pytest.mark.asyncio
async def test_create_user_already_exists(user_repository, mock_session, test_user):
    user_data = UserCreate(
        username="testuser",
        email="test@test.com",
        password="testpassword",
        role=UserRole.USER,
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = test_user  # user already exists
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repository.create_user(
        user_data, "https://example.com/avatar.jpg"
    )
    assert result is None


@pytest.mark.asyncio
async def test_confirm_email(user_repository, mock_session, test_user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = test_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    user = await user_repository.confirmed_email("test@test.com")

    assert user is not None
    assert user.confirmed_email is True
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_avatar(user_repository, mock_session, test_user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = test_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    user = await user_repository.update_avatar(
        "test@test.com", "https://newavatar.com/avatar.jpg"
    )

    assert user is not None
    assert test_user.avatar == "https://newavatar.com/avatar.jpg"
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_reset_password(user_repository, mock_session, test_user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = test_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    await user_repository.reset_password(
        "newpassword",
        "test@test.com",
    )

    assert test_user.password == "newpassword"
    mock_session.commit.assert_awaited_once()
