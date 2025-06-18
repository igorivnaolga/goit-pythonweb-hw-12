from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from typing import Self


class Settings(BaseSettings):
    # DB
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_PORT: str
    POSTGRES_HOST: str
    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str
    JWT_EXPIRATION_SECONDS: int
    # EMAIL
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: str
    MAIL_SERVER: str
    MAIL_FROM_NAME: str
    MAIL_STARTTLS: bool
    MAIL_SSL_TLS: bool
    MAIL_USE_CREDENTIALS: bool
    MAIL_VALIDATE_CERTS: bool
    # CLOUDINARY
    CLOUDINARY_NAME: str
    CLOUDINARY_API_KEY: int
    CLOUDINARY_API_SECRET: str
    # REDIS
    REDIS_HOST: str
    REDIS_PORT: str
    # CONFIG
    model_config = ConfigDict(
        extra="ignore", env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )

    @property
    def database_url(self: Self):
        """
        Assemble a connection string for SQLAlchemy from the environment variables.

        :return: A connection string for SQLAlchemy.
        :rtype: str
        """
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()
