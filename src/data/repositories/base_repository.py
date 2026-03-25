from typing import Any

from sqlalchemy import and_, insert, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions.exceptions import AppException, ConflictException, NotFoundException


async def commit_transaction(db: AsyncSession) -> None:
    try:
        await db.commit()
    except Exception as err:
        await db.rollback()
        raise AppException(detail=f"Commit failed {str(err)}") from err


async def insert_data(model: type[Any], db: AsyncSession, **kwargs: Any) -> None:
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
