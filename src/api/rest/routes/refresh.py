from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.rest.dependencies import get_db
from src.core.services.token_service import refresh_access_token

refresh_router = APIRouter()

@refresh_router.get("/refresh")
async def refresh_token(request: Request, db: AsyncSession = Depends(get_db)):
    await refresh_access_token(request, db)