"""This module defines dependencies for the PayU Authentication Service, specifically providing a dependency for obtaining an asynchronous database session. The `get_db` function is an asynchronous generator that yields an instance of `AsyncSession` from SQLAlchemy, allowing route handlers to access the database session for performing database operations. The function ensures that the database session is properly closed after use, preventing potential resource leaks. By including this dependency in route handlers, we can easily manage database sessions and ensure that they are correctly handled throughout the lifecycle of each request."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.data.clients.database import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an asynchronous database session.
    This function is an asynchronous generator that yields a database session. It ensures that the session is properly closed after use, preventing potential resource leaks. Route handlers that require database access can include this dependency to receive a session instance.
    Yields:
        An instance of AsyncSession for database operations.
    """
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()
