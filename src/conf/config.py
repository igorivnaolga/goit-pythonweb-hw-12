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
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()


# import configparser

# # Load config.ini
# parser = configparser.ConfigParser()
# parser.read("src/conf/config.ini")

# # Read DB credentials from the config file
# db_user = parser.get("DB", "USER")
# db_password = parser.get("DB", "PASSWORD")
# db_name = parser.get("DB", "DB_NAME")
# db_host = parser.get("DB", "DOMAIN")
# db_port = parser.get("DB", "PORT")


# class Config:
#     DB_URL = (
#         f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
#     )
#     JWT_SECRET = "your_secret_key"  # Секретний ключ для токенів
#     JWT_ALGORITHM = "HS256"  # Алгоритм шифрування токенів
#     JWT_EXPIRATION_SECONDS = 3600  # Час дії токена (1 година)


# config = Config
