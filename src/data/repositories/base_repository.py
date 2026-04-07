"""This module defines a set of utility functions for performing common database operations using SQLAlchemy's asynchronous session. These functions include committing transactions, inserting data, updating data by ID or by any specified conditions, and retrieving data by ID or by any specified conditions. Each function is designed to handle exceptions gracefully, rolling back transactions when necessary and raising appropriate custom exceptions to provide clear error messages. By centralizing these database operations in a base repository module, we can promote code reuse and maintain a consistent approach to database interactions across the application. This helps to simplify error handling and improve the overall robustness of the application's data access layer, ensuring that all database operations are performed efficiently and securely while providing meaningful feedback in case of errors."""

from typing import Any

from sqlalchemy import and_, insert, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions.exceptions import AppException, ConflictException, NotFoundException


async def commit_transaction(db: AsyncSession) -> None:
    """Commit the current transaction in the database session. This function attempts to commit the transaction and handles any exceptions that may occur during the commit process. If an IntegrityError occurs (e.g., due to a unique constraint violation), it rolls back the transaction and raises a ConflictException with details of the error. For any other SQLAlchemy-related errors, it also rolls back the transaction and raises a generic AppException with the error details.    Args:
    db: An instance of AsyncSession representing the current database session.    Raises:
    ConflictException: If an integrity error occurs during the commit operation, such as a unique constraint violation.    AppException: If any other SQLAlchemy-related error occurs during the commit operation."""
    try:
        await db.commit()
    except Exception as err:
        await db.rollback()
        raise AppException(detail=f"Commit failed {str(err)}") from err


async def insert_data(model: type[Any], db: AsyncSession, **kwargs: Any) -> None:
    """Insert data into the database using the specified model and keyword arguments. This function attempts to insert a new record into the database based on the provided model and data. If an integrity error occurs (e.g., due to a unique constraint violation), it rolls back the transaction and raises a ConflictException with details of the error. For any other SQLAlchemy-related errors, it also rolls back the transaction and raises a generic AppException with the error details.    Args:       model: The SQLAlchemy model class representing the database table into which the data should be inserted.    db: An instance of AsyncSession for interacting with the database.    **kwargs: Keyword arguments representing the data to be inserted, where keys correspond to column names in the database table.    Raises:       ConflictException: If an integrity error occurs during the insert operation, such as a unique constraint violation.    AppException: If any other SQLAlchemy-related error occurs during the insert operation."""
    try:
        stmt = insert(model).values(**kwargs)
        await db.execute(stmt)
        await commit_transaction(db)
    except IntegrityError as err:
        await db.rollback()
        raise ConflictException(detail=str(err)) from err
    except SQLAlchemyError as err:
        await db.rollback()
        raise AppException(detail=str(err)) from err


async def update_data_by_id(model: type[Any], id: int, db: AsyncSession, **kwargs: Any) -> None:
    """Update data in the database based on the specified model and ID. This function attempts to update an existing record in the database by matching the provided ID with the primary key of the model. If no record is found with the given ID, it raises a NotFoundException. If any SQLAlchemy-related errors occur during the update process, it rolls back the transaction and raises a generic AppException with the error details.    Args:
    model: The SQLAlchemy model class representing the database table to be updated.    id: The unique identifier of the record to be updated.    db: An instance of AsyncSession for interacting with the database.    **kwargs: Keyword arguments representing the data to be updated, where keys correspond to column names in the database table.    Raises:
    NotFoundException: If no record is found with the given ID.    AppException: If any SQLAlchemy-related error occurs during the update               operation."""
    try:
        stmt = update(model).where(model.id == id).values(**kwargs)
        result = await db.execute(stmt)

        if getattr(result, "rowcount", 0) == 0:
            raise NotFoundException(detail="Data not found")

        await commit_transaction(db)
    except SQLAlchemyError as err:
        await db.rollback()
        raise AppException(detail=str(err)) from err


async def update_data_by_any(
    model: type[Any], db: AsyncSession, data: dict[str, Any], **kwargs: Any
) -> None:
    """Update data in the database based on the specified model and conditions. This function attempts to update existing records in the database by matching the provided conditions (data) with the corresponding columns in the model. If no records are found that match the given conditions, it raises a NotFoundException. If any SQLAlchemy-related errors occur during the update process, it rolls back the transaction and raises a generic AppException with the error details.    Args:
    model: The SQLAlchemy model class representing the database table to be updated.    db: An instance of AsyncSession for interacting with the database.    data: A dictionary containing the conditions to match for the update operation, where keys correspond to column names and values correspond to the values to be matched.    **kwargs: Keyword arguments representing the data to be updated, where keys correspond to column names in the database table.    Raises:
    NotFoundException: If no records are found that match the given conditions.    AppException: If any SQLAlchemy-related error occurs during the update operation."""
    try:
        conditions = []
        for key, value in data.items():
            column = getattr(model, key)
            conditions.append(column == value)

        stmt = update(model).where(and_(*conditions)).values(**kwargs)
        result = await db.execute(stmt)

        if getattr(result, "rowcount", 0) == 0:
            raise NotFoundException(detail="Data not found")

        await commit_transaction(db)
    except SQLAlchemyError as err:
        raise AppException(detail=str(err)) from err


async def get_data_by_id(model: type[Any], id: int, db: AsyncSession) -> Any:
    """Retrieve a record from the database based on the specified model and ID. This function attempts to fetch a single record from the database by matching the provided ID with the primary key of the model. If no record is found with the given ID, it raises a NotFoundException. If any SQLAlchemy-related errors occur during the retrieval process, it raises a generic AppException with the error details.    Args:
    model: The SQLAlchemy model class representing the database table to query.    id: The unique identifier of the record to be retrieved.    db: An instance of AsyncSession for interacting with the database.    Returns:
    The record retrieved from the database if found.    Raises:
    NotFoundException: If no record is found with the given ID.    AppException: If any SQLAlchemy-related error occurs during the retrieval operation."""
    try:
        stmt = select(model).where(model.id == id)
        result = await db.execute(stmt)
        obj = result.scalar_one_or_none()

        if not obj:
            raise NotFoundException(detail="Data not found")

        return obj
    except SQLAlchemyError as err:
        raise AppException(detail=str(err)) from err


async def get_data_by_any(model: type[Any], db: AsyncSession, **kwargs: Any) -> Any:
    """Retrieve a record from the database based on the specified model and conditions. This function attempts to fetch a single record from the database by matching the provided conditions (kwargs) with the corresponding columns in the model. If no record is found that matches the given conditions, it raises a NotFoundException. If any SQLAlchemy-related errors occur during the retrieval process, it raises a generic AppException with the error details.    Args:
    model: The SQLAlchemy model class representing the database table to query.    db: An instance of AsyncSession for interacting with the database.    **kwargs: Keyword arguments representing the conditions to match for the retrieval operation, where keys correspond to column names and values correspond to the values to be matched.    Returns:
    The record retrieved from the database if found.    Raises:
    NotFoundException: If no record is found that matches the given conditions.    AppException: If any SQLAlchemy-related error occurs during the retrieval operation."""
    try:
        conditions = []
        for key, value in kwargs.items():
            column = getattr(model, key)
            conditions.append(column == value)

        stmt = select(model).where(and_(*conditions))
        result = await db.execute(stmt)
        obj = result.scalar_one_or_none()

        if not obj:
            raise NotFoundException(detail="Data not found")

        return obj
    except SQLAlchemyError as err:
        raise AppException(detail=str(err)) from err
