"""This module contains the core business logic for user-related operations in the PayU Authentication Service. It provides functions for creating new users, handling user login and logout, and retrieving user profiles. The functions interact with the database using SQLAlchemy's asynchronous session and handle various exceptions that may arise during these operations. The module also integrates with the JWT handling functions to manage access and refresh tokens for authentication purposes. Each function is designed to return appropriate responses or raise exceptions based on the outcome of the operations, ensuring a robust and secure user management system within the authentication service."""

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
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
    """Create a new user in the database. This function takes a UserRequest object containing the user's details and an asynchronous database session. It hashes the user's password and attempts to insert the new user record into the database. If the operation is successful, it returns a success message. If any exceptions occur during this process, such as database connection issues or integrity errors, it raises an AppException with the error details.    Args:
    user: A UserRequest object containing the user's name, email, password, and role.    db: An instance of AsyncSession for interacting with the database.    Returns:
    A dictionary containing a success message if the user is created successfully.    Raises:
    AppException: If any error occurs while creating the user in the database, such as database connection issues or integrity errors."""
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
    """Handle user login by verifying credentials and generating access and refresh tokens. This function takes a LoginRequest object containing the user's email and password, and an asynchronous database session. It retrieves the user from the database based on the provided email, verifies the password, and if valid, generates JWT access and refresh tokens. The refresh token is saved in the database for future validation. The function returns a JSON response containing the access token, refresh token, and user information. If any issues arise during this process, such as invalid credentials or token generation failures, appropriate exceptions are raised with detailed error messages.    Args:
    request: A LoginRequest object containing the user's email and password.    db: An instance of AsyncSession for interacting with the database.    Returns:
    A JSONResponse containing the access token, refresh token, and user information if login is successful.    Raises:
    UnauthorizedException: If the provided credentials are invalid.    AppException: If any error occurs during the login process, such as database connection issues or token generation failures."""
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
    """Handle user logout by revoking the refresh token and deactivating the user. This function takes an HTTP request containing the refresh token in its cookies and an asynchronous database session. It verifies the refresh token, marks it as revoked in the database, and sets the user's active status to False. The function then returns a JSON response indicating that the logout was successful and deletes the access and refresh tokens from the client's cookies. If any issues arise during this process, such as a missing or invalid refresh token, or if any database errors occur, appropriate exceptions are raised with detailed error messages.    Args:
    request: The incoming HTTP request containing the refresh token in its cookies.    db: An instance of AsyncSession for interacting with the database.    Returns:
    A JSONResponse indicating that the logout was successful, with the access and refresh tokens deleted from the client's cookies.    Raises:
    BadRequestException: If the refresh token is missing from the request cookies.    UnauthorizedException: If the refresh token is invalid.    AppException: If any error occurs during the logout process, such as database connection issues or token revocation failures."""
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
    """Retrieve the profile information of a user based on their user ID. This function takes a user ID and an asynchronous database session, and attempts to fetch the user's information from the database. If the user is found, it returns a dictionary containing the user's ID, name, email, role, and active status. If any issues arise during this process, such as the user not being found or database errors, appropriate exceptions are raised with detailed error messages.    Args:
    user_id: The ID of the user whose profile information is to be retrieved.    db: An instance of AsyncSession for interacting with the database.    Returns:
    A dictionary containing the user's ID, name, email, role, and active status if the user is found.    Raises:
    BadRequestException: If the user cannot be found in the database.    AppException: If any error occurs during the retrieval process, such as database connection issues or query failures."""
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
