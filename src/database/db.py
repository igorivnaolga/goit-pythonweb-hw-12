import contextlib

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from src.conf.config import settings


class DatabaseSessionManager:
    def __init__(self, url: str):
        """
        Initializes the database session manager.

        Args:
            url (str): The SQLAlchemy connection URL.
        """
        self._engine: AsyncEngine | None = create_async_engine(url)
        self._session_maker: async_sessionmaker = async_sessionmaker(
            autoflush=False, autocommit=False, bind=self._engine
        )

    @contextlib.asynccontextmanager
    async def session(self):
        """
        Provide a transactional scope around a series of operations.

        This async context manager yields a new database session, allowing for
        operations to be performed within a transaction. In the event of an
        exception, the transaction is rolled back. Regardless of success or
        failure, the session is always closed upon completion of the block.

        Yields:
            AsyncSession: A new SQLAlchemy async session for database operations.

        Raises:
            Exception: If the session maker is not initialized.
            SQLAlchemyError: If an error occurs during the transaction, which
            is then re-raised after rollback.
        """
        if self._session_maker is None:
            raise Exception("Database session is not initialized")
        session = self._session_maker()
        try:
            yield session
        except SQLAlchemyError as e:
            await session.rollback()
            raise  # Re-raise the original error
        finally:
            await session.close()


sessionmanager = DatabaseSessionManager(settings.database_url)


async def get_db():
    """
    Asynchronous dependency for FastAPI that yields a database session.

    Returns:
        AsyncSession: A new database session for database operations.
    """
    async with sessionmanager.session() as session:
        yield session
