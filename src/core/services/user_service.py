from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config.settings import settings
from src.core.exceptions.exceptions import AppException, BadRequestException, UnauthorizedException
from src.core.security.hashing import hash_data, verify_data
from src.core.security.jwt_handler import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from src.data.models.token_model import RefreshToken
from src.data.models.user_model import User
from src.data.repositories.base_repository import (
    get_data_by_any,
    get_data_by_id,
    insert_data,
    update_data_by_any,
    update_data_by_id,
)
from src.schemas.user_schema import LoginRequest, UserRequest


async def createUser(user: UserRequest, db: AsyncSession) -> dict[str, str]:
    try:
        data: dict[str, Any] = {
            "name": user.name,
            "email": user.email,
            "password": hash_data(user.password),
            "role": user.role,
        }

        await insert_data(User, db, **data)

        return {"message": "User created successfully"}

    except SQLAlchemyError as err:
        raise AppException(detail=str(err)) from err


async def login(request: LoginRequest, db: AsyncSession) -> JSONResponse:
    try:
        data: dict[str, Any] = {"email": request.email}
        user = await get_data_by_any(User, db, **data)

        if not user or not verify_data(request.password, user.password):
            raise UnauthorizedException(detail="Invalid credentials")

        access = create_access_token({"sub": user.email, "user_id": user.id})
        refresh = create_refresh_token({"sub": user.email, "user_id": user.id})


        if not access or not refresh:
            raise AppException(detail="Token generation failed")

        access_token, _, _ = access
        refresh_token, refresh_jti, refresh_expire = refresh

        await insert_data(
            RefreshToken,
            db,
            user_id=user.id,
            jti=refresh_jti,
            expires_at=refresh_expire,
        )

        await update_data_by_id(User, user.id, db, is_active=True)

        user = await get_data_by_id(User, user.id, db)

        user_data: dict[str, Any] = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
        }

        response = JSONResponse(
            {
                "message": "Login successful",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "user": user_data,
            }
        )

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            samesite="none",
            secure=True,
            path="/",
            max_age=settings.access_token_expire_minutes * 60,
        )

        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            samesite="none",
            secure=True,
            path="/",
            max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        )

        return response

    except SQLAlchemyError as err:
        raise AppException(detail=str(err)) from err


async def logout(request: Request, db: AsyncSession) -> JSONResponse:
    try:
        refresh_token = request.cookies.get("refresh_token")

        if not refresh_token:
            raise BadRequestException(detail="No user found")

        payload = verify_refresh_token(refresh_token)
        if not payload:
            raise UnauthorizedException(detail="Invalid token")

        user_id: int = payload["user_id"]

        await update_data_by_any(
            RefreshToken,
            db,
            {"jti": payload["jti"]},
            is_revoked=True,
        )

        await update_data_by_id(User, user_id, db, is_active=False)

        response = JSONResponse({"message": "User logout successful"})
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")

        return response

    except SQLAlchemyError as err:
        raise AppException(detail=str(err)) from err


async def getProfile(user_id: int, db: AsyncSession) -> dict[str, Any]:
    try:
        result = await get_data_by_id(User, user_id, db)

        return {
            "id": result.id,
            "name": result.name,
            "email": result.email,
            "role": result.role,
            "is_active": result.is_active,
        }

    except SQLAlchemyError as err:
        raise BadRequestException(detail=str(err)) from err
