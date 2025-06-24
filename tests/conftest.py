import asyncio
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import pytest_asyncio
from pydantic import computed_field
from pydantic_settings import SettingsConfigDict
import pytest

from src.conf.config import Settings


class TestSettings(Settings):
    TITLE: str
    SECRET_KEY: str
    JWT_SECRET: str
    JWT_ALGORITHM: str
    JWT_EXPIRATION_SECONDS: int

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_TEMPLATE_DB: str
    POSTGRES_PORT_EXTERNAL: int | None = None

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PORT_EXTERNAL: int | None = None
    REDIS_URI: str

    DATABASE_URI: str

    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_FROM_NAME: str
    MAIL_STARTTLS: bool
    MAIL_SSL_TLS: bool
    MAIL_USE_CREDENTIALS: bool
    MAIL_VALIDATE_CERTS: bool

    CLOUDINARY_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    USE_TESTCONTAINERS: bool
    POSTGRES_DOCKER_IMAGE: str
    REDIS_DOCKER_IMAGE: str
    ACCESS_TOKEN_EXP_MINUTES: int

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".testenv"
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def get_template_postgres_uri(self) -> str:
        """Build database URI for DB template."""
        parsed = urlparse(self.DATABASE_URI)
        netloc = f"{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}"
        path = f"/{self.POSTGRES_TEMPLATE_DB}"
        return urlunparse((parsed.scheme, netloc, path, "", "", ""))


@pytest_asyncio.fixture(scope="session")
async def anyio_backend() -> str:
    return "asyncio"


@pytest_asyncio.fixture(scope="session", autouse=False)
async def test_settings() -> TestSettings:
    """Settings for tests."""
    return TestSettings()


@pytest.fixture(scope="session", autouse=True)
def _debug_settings(test_settings: TestSettings):
    print("🧪 DEBUG SETTINGS:")
    print("   USER:", test_settings.POSTGRES_USER)
    print("   PASS:", test_settings.POSTGRES_PASSWORD)
    print("   DB URI:", test_settings.DATABASE_URI)


from pathlib import Path


print("I am in ", Path(__file__))
