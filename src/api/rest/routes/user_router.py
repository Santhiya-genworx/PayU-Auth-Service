from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies import get_db
from src.core.security.jwt_handler import get_current_user
from src.core.services.user_service import createUser, getProfile, login, logout
from src.schemas.user_schema import LoginRequest, UserRequest

user_router = APIRouter(prefix="/users")


@user_router.post("/create")
async def create_user(
    user: UserRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    return await createUser(user, db)


@user_router.put("/login")
async def user_login(
    user: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    return await login(user, db)


@user_router.put("/logout")
async def user_logout(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    return await logout(request, db)


@user_router.get("/me")
async def get_me(
    current_user: dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await getProfile(current_user["id"], db)
