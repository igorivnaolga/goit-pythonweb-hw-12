import os
from pathlib import Path
from unittest.mock import AsyncMock
from urllib.parse import urlparse, urlunparse
from redis import Redis
import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
)
from testcontainers.core.generic import DbContainer  # type: ignore[import-untyped]
from testcontainers.postgres import PostgresContainer  # type: ignore[import-untyped]
from testcontainers.redis import RedisContainer  # type: ignore[import-untyped]

from src.conf.config import get_settings
from src.database.db import DatabaseSessionManager, get_db
from src.database.models import User
from src.services.auth import auth_service
from tests.conftest import TestSettings
from tests.factories import UserFactory
from src.schemas.users import UserCreate
from tests.integration.test_integration_auth import confirm_user


DROP_DATABASE_SQL = """DROP DATABASE IF EXISTS {name};"""
SET_IS_TEMPLATE_SQL = """ALTER DATABASE {name} WITH is_template = true;"""
COPY_DATABASE_SQL = """CREATE DATABASE {name} TEMPLATE {template};"""


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def _database_container_instance(
    test_settings: TestSettings,
) -> PostgresContainer | None:
    if not test_settings.USE_TESTCONTAINERS:
        return None

    container = PostgresContainer(
        image=test_settings.POSTGRES_DOCKER_IMAGE,
        dbname=test_settings.POSTGRES_TEMPLATE_DB,
        username=test_settings.POSTGRES_USER,
        password=test_settings.POSTGRES_PASSWORD,
    )

    if test_settings.POSTGRES_PORT_EXTERNAL:
        container.with_bind_ports(5432, test_settings.POSTGRES_PORT_EXTERNAL)

    container.start()

    hostname = container.get_container_host_ip()
    port = int(container.get_exposed_port(5432))

    test_settings.DATABASE_URI = (
        f"postgresql+asyncpg://{test_settings.POSTGRES_USER}:{test_settings.POSTGRES_PASSWORD}"
        f"@{hostname}:{port}/{test_settings.POSTGRES_DB}"
    )

    test_settings.POSTGRES_HOST = hostname
    test_settings.POSTGRES_PORT = port

    return container


@pytest_asyncio.fixture(scope="session")
async def _setup_template_database(test_settings: TestSettings):
    engine = create_async_engine(
        url=test_settings.get_template_postgres_uri, echo=False
    )
    async with engine.begin() as conn:
        await conn.execute(
            text(SET_IS_TEMPLATE_SQL.format(name=test_settings.POSTGRES_TEMPLATE_DB))
        )
        # ❗ НЕ видаляємо таблиці, щоб залишити структуру для шаблону
    await engine.dispose()


def apply_migrations(db_uri: str) -> None:
    print("=" * 60)
    print(f"📦 Applying Alembic migrations to: {db_uri}")
    print("=" * 60)
    alembic_cfg = Config(str(Path(__file__).parent.parent.parent / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", "migrations")
    alembic_cfg.set_main_option("sqlalchemy.url", db_uri)
    command.upgrade(alembic_cfg, "head")


@pytest.fixture(scope="session")
def _migrate_template_database(_setup_template_database, test_settings: TestSettings):
    apply_migrations(test_settings.get_template_postgres_uri)


@pytest_asyncio.fixture(scope="function")
async def _copy_database(_migrate_template_database, test_settings: TestSettings):
    engine = create_async_engine(
        url=test_settings.get_template_postgres_uri, echo=False
    )
    async with engine.connect() as conn:
        await conn.execution_options(isolation_level="AUTOCOMMIT")
        await conn.execute(
            text(
                f"""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = '{test_settings.POSTGRES_DB}' AND pid <> pg_backend_pid();
        """
            )
        )
        await conn.execute(
            text(DROP_DATABASE_SQL.format(name=test_settings.POSTGRES_DB))
        )
        await conn.execute(
            text(
                COPY_DATABASE_SQL.format(
                    name=test_settings.POSTGRES_DB,
                    template=test_settings.POSTGRES_TEMPLATE_DB,
                )
            )
        )
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_db(_copy_database, test_settings: TestSettings):
    test_sessionmanager = DatabaseSessionManager(test_settings.DATABASE_URI)
    async with test_sessionmanager.session() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def test_cache(test_settings: TestSettings):
    redis_client = Redis.from_url(url=test_settings.REDIS_URI, decode_responses=True)
    yield redis_client
    await redis_client.close()


@pytest.fixture(scope="function")
def test_app(_copy_database, test_db, test_settings: TestSettings) -> FastAPI:
    from main import app as fastapi_app

    def override_get_settings() -> TestSettings:
        return test_settings

    def override_get_db():
        return test_db

    fastapi_app.dependency_overrides[get_settings] = override_get_settings
    fastapi_app.dependency_overrides[get_db] = override_get_db
    return fastapi_app


@pytest_asyncio.fixture
async def unauthenticated_client(test_app) -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        yield client


@pytest_asyncio.fixture
async def test_user(test_db):
    user_data = UserCreate(
        username="testuser",
        email="testuser@example.com",
        password="testpassword123",
        role="user",
    )
    hashed_password = auth_service.get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        password=hashed_password,
        role=user_data.role,
        confirmed_email=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return {
        "username": user.username,
        "email": user.email,
        "password": user_data.password,
        "role": user.role,
        "avatar": "https://example.com/avatar.jpg",
    }


@pytest_asyncio.fixture
async def test_client(test_app, test_db, test_user):
    await confirm_user(test_db, test_user["email"])

    access_token = await auth_service.create_access_token(
        {"sub": test_user["email"]}, 30
    )

    headers = {"Authorization": f"Bearer {access_token}"}
    transport = ASGITransport(app=test_app)
    async with AsyncClient(
        transport=transport, base_url="http://test", headers=headers
    ) as client:
        yield client


# DROP_TABLE_SQL = """DROP TABLE IF EXISTS {name} CASCADE;"""
# SET_IS_TEMPLATE_SQL = """ALTER DATABASE {name} WITH is_template = true;"""
# DROP_DATABASE_SQL = """DROP DATABASE IF EXISTS {name};"""
# COPY_DATABASE_SQL = """CREATE DATABASE {name} TEMPLATE {template};"""


# @pytest.fixture(scope="session")
# def event_loop():
#     loop = asyncio.new_event_loop()
#     yield loop
#     loop.close()


# @pytest.fixture(scope="session", autouse=True)
# def _database_container_instance(
#     test_settings: TestSettings,
# ) -> PostgresContainer | None:
#     if not test_settings.USE_TESTCONTAINERS:
#         return None

#     # Створюємо контейнер із правильними параметрами
#     container = PostgresContainer(
#         image=test_settings.POSTGRES_DOCKER_IMAGE,
#         dbname=test_settings.POSTGRES_TEMPLATE_DB,
#         username=test_settings.POSTGRES_USER,
#         password=test_settings.POSTGRES_PASSWORD,
#     )

#     if test_settings.POSTGRES_PORT_EXTERNAL:
#         container.with_bind_ports(5432, test_settings.POSTGRES_PORT_EXTERNAL)

#     container.start()

#     # Отримуємо реальні хост і порт
#     hostname = container.get_container_host_ip()
#     port = int(container.get_exposed_port(5432))

#     # 🔥 Оновлюємо URI після старту контейнера!
#     test_settings.DATABASE_URI = (
#         f"postgresql+asyncpg://{test_settings.POSTGRES_USER}:{test_settings.POSTGRES_PASSWORD}"
#         f"@{hostname}:{port}/{test_settings.POSTGRES_DB}"
#     )

#     # Теж оновимо get_template_postgres_uri, якщо треба
#     test_settings.POSTGRES_HOST = hostname
#     test_settings.POSTGRES_PORT = port

#     return container


# @pytest_asyncio.fixture(scope="session")
# async def _setup_template_database(test_settings: TestSettings):
#     engine = create_async_engine(
#         url=test_settings.get_template_postgres_uri, echo=False
#     )
#     async with engine.begin() as conn:
#         await conn.execute(
#             text(SET_IS_TEMPLATE_SQL.format(name=test_settings.POSTGRES_TEMPLATE_DB))
#         )
#         # await conn.execute(text(DROP_TABLE_SQL.format(name="alembic_version")))
#         # from migrations.metadata import target_metadata

#         # await conn.run_sync(target_metadata.drop_all)
#     await engine.dispose()


# def apply_migrations(db_uri: str) -> None:
#     print("=" * 60)
#     print(f"📦 Applying Alembic migrations to: {db_uri}")
#     print("=" * 60)
#     alembic_cfg = Config(str(Path(__file__).parent.parent.parent / "alembic.ini"))
#     alembic_cfg.set_main_option("script_location", "migrations")
#     alembic_cfg.set_main_option("sqlalchemy.url", db_uri)
#     command.upgrade(alembic_cfg, "head")


# @pytest.fixture(scope="session")
# def _migrate_template_database(_setup_template_database, test_settings: TestSettings):
#     apply_migrations(test_settings.get_template_postgres_uri)


# @pytest_asyncio.fixture(scope="function")
# async def _copy_database(_migrate_template_database, test_settings: TestSettings):
#     engine = create_async_engine(
#         url=test_settings.get_template_postgres_uri, echo=False
#     )
#     async with engine.connect() as conn:
#         await conn.execution_options(isolation_level="AUTOCOMMIT")
#         await conn.execute(
#             text(
#                 f"""
#             SELECT pg_terminate_backend(pid)
#             FROM pg_stat_activity
#             WHERE datname = '{test_settings.POSTGRES_DB}' AND pid <> pg_backend_pid();
#             """
#             )
#         )
#         await conn.execute(
#             text(DROP_DATABASE_SQL.format(name=test_settings.POSTGRES_DB))
#         )
#         await conn.execute(
#             text(
#                 COPY_DATABASE_SQL.format(
#                     name=test_settings.POSTGRES_DB,
#                     template=test_settings.POSTGRES_TEMPLATE_DB,
#                 )
#             )
#         )
#     await engine.dispose()


# @pytest_asyncio.fixture(scope="function")
# async def test_db(_copy_database, test_settings: TestSettings):
#     test_sessionmanager = DatabaseSessionManager(test_settings.DATABASE_URI)
#     async with test_sessionmanager.session() as session:
#         yield session


# @pytest_asyncio.fixture(scope="function")
# async def test_cache(test_settings: TestSettings):
#     redis_client = Redis.from_url(url=test_settings.REDIS_URI, decode_responses=True)
#     yield redis_client
#     redis_client.close()


# @pytest.fixture(scope="function")
# def test_app(_copy_database, test_db, test_settings: TestSettings) -> FastAPI:
#     from main import app as fastapi_app

#     def override_get_settings() -> TestSettings:
#         return test_settings

#     def override_get_db():
#         return test_db

#     fastapi_app.dependency_overrides[get_settings] = override_get_settings
#     fastapi_app.dependency_overrides[get_db] = override_get_db
#     return fastapi_app


# @pytest.fixture(scope="function")
# def unauthenticated_client(test_app: FastAPI) -> AsyncClient:
#     return AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test")


# @pytest_asyncio.fixture
# async def test_client(test_db, test_user):
#     await confirm_user(test_db, test_user["email"])

#     access_token = await auth_service.create_access_token(
#         {"sub": test_user["email"]}, 30
#     )

#     headers = {"Authorization": f"Bearer {access_token}"}
#     async with AsyncClient(base_url="http://test", headers=headers) as client:
#         yield client


# @pytest_asyncio.fixture
# async def test_user(test_db):
#     user_data = UserCreate(
#         username="testuser",
#         email="testuser@example.com",
#         password="testpassword123",
#         role="user",
#     )
#     hashed_password = auth_service.get_password_hash(user_data.password)
#     user = User(
#         username=user_data.username,
#         email=user_data.email,
#         password=hashed_password,
#         role=user_data.role,
#         confirmed_email=True,
#     )
#     test_db.add(user)
#     await test_db.commit()
#     await test_db.refresh(user)
#     return {
#         "username": user.username,
#         "email": user.email,
#         "password": user_data.password,
#         "role": user.role,
#         "avatar": "https://example.com/avatar.jpg",
#     }


# print("I am in ", Path(__file__))
