from fastapi import APIRouter, Depends, Request
from src.core.security.jwt_handler import get_current_user
from src.api.rest.dependencies import get_db
from src.schemas.user_schema import LoginRequest, UserRequest, UserResponse
from src.core.services.user_service import createUser, login, logout
from sqlalchemy.ext.asyncio import AsyncSession

user_router = APIRouter(prefix="/users")

@user_router.post("/create")
async def create_user(user: UserRequest, db: AsyncSession = Depends(get_db)):
    return await createUser(user, db)

@user_router.put("/login")
async def user_login(user: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await login(user, db)

@user_router.put("/logout")
async def user_logout(request: Request, db: AsyncSession = Depends(get_db)):
    return await logout(request, db)

@user_router.get("/me")
async def get_me(current_user = Depends(get_current_user)):
    return current_user