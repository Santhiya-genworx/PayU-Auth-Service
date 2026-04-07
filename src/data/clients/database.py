"""This module sets up the database connection and defines the base class for SQLAlchemy models in the PayU Authentication Service. It uses SQLAlchemy's asynchronous capabilities to create an asynchronous engine and session maker for interacting with the database. The Base class serves as the declarative base for all ORM models, allowing them to be defined with SQLAlchemy's ORM features. The init_db function is responsible for applying any pending database migrations when the application starts, ensuring that the database schema is up to date with the defined models. This setup allows for efficient and scalable database interactions while maintaining a clear structure for defining and managing database models within the authentication service."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config.settings import settings
from src.data.migrations.runner import apply_migrations

engine = create_async_engine(settings.db_url)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models. All database models should inherit from this class to ensure they are properly registered with SQLAlchemy's ORM system. This class serves as a common base for all models, allowing for consistent behavior and easy integration with the database session."""

    pass


engine = create_async_engine(
    settings.db_url,
    pool_pre_ping=True,
)


async def init_db() -> None:
    """Initialize the database by applying any pending migrations. This function creates an asynchronous connection to the database and runs the migration scripts to ensure that the database schema is up to date with the application's requirements. It should be called during application startup to prepare the database for use."""
    async with engine.begin() as conn:
        await apply_migrations(conn)
