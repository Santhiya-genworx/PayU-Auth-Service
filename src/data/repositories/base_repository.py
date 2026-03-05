from typing import Type
from fastapi import HTTPException
from sqlalchemy import and_, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

async def commit_transaction(db: AsyncSession):
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Commit failed {str(e)}")

async def insert_data(model: Type, db: AsyncSession, **kwargs):
    try:
        stmt = insert(model).values(**kwargs)
        await db.execute(stmt)
        await commit_transaction(db)
    except IntegrityError as err:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(err))
    except SQLAlchemyError as err:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(err))

async def update_data_by_id(model: Type, id: int, db: AsyncSession, **kwargs):
    try:
        stmt = update(model).where(model.id==id).values(**kwargs)
        result = await db.execute(stmt)
        if result.rowcount == 0:
            raise HTTPException(status_code=404,detail="Data not found")
        await commit_transaction(db)
    except SQLAlchemyError as err:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(err))
    
async def update_data_by_any(model: Type, db: AsyncSession, data: dict, **kwargs):
    try:
        conditions = []
        for key, value in data.items():
            column = getattr(model, key)
            conditions.append(column == value)
        
        stmt = update(model).where(and_(*conditions)).values(**kwargs)
        result = await db.execute(stmt)
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Data not found")
        await commit_transaction(db)
    except SQLAlchemyError as err:
        raise HTTPException(status_code=500, detail=str(err))
    
async def get_data_by_id(model: Type, id: int, db: AsyncSession):
    try:
        stmt = select(model).where(model.id==id)
        result = await db.execute(stmt)
        result = result.scalar_one_or_none()
        if not result:
            raise HTTPException(status_code=404, detail="Data not found")
        return result
    except SQLAlchemyError as err:
        raise HTTPException(status_code=500,detail=str(err))
    
async def get_data_by_any(model: Type, db: AsyncSession, **kwargs):
    try:
        conditions = []
        for key, value in kwargs.items():
            column = getattr(model, key)
            conditions.append(column == value)
        
        stmt = select(model).where(and_(*conditions))
        result = await db.execute(stmt)
        result = result.scalar_one_or_none()
        if not result:
            raise HTTPException(status_code=404, detail="Data not found")
        return result
    except SQLAlchemyError as err:
        raise HTTPException(status_code=500, detail=str(err))