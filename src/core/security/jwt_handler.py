"""This module provides functions for handling JSON Web Tokens (JWT) in the PayU Authentication Service. It includes functions for creating access and refresh tokens, verifying their validity, and retrieving the current user based on the token payload. The module uses the jose library for encoding and decoding JWTs, and interacts with the database to fetch user information when needed. It also includes error handling to ensure that any issues with token processing are properly managed and reported. This module is a key component of the authentication system, enabling secure token-based authentication for users of the service."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import Depends, Request
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies import get_db
from src.config.settings import settings
from src.core.exceptions.exceptions import NotFoundException, UnauthorizedException
from src.data.models.user_model import User
from src.data.repositories.base_repository import get_data_by_id


def create_access_token(data: dict[str, Any]) -> tuple[str, str, datetime] | None:
    """Create an access token for the given data.
    Args:
        data: A dictionary containing the data to be encoded in the token.
    Returns:
        A tuple containing the access token, its unique identifier, and expiration time, or None if token creation fails.
    """
    try:
        to_encode = data.copy()
        expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
        jti = str(uuid.uuid4())

        to_encode.update({"exp": expire, "type": "access", "jti": jti})
        token = jwt.encode(to_encode, settings.access_secret_key, algorithm=settings.algorithm)
        return token, jti, expire
    except JWTError:
        return None


def create_refresh_token(data: dict[str, Any]) -> tuple[str, str, datetime] | None:
    """Create a refresh token for the given data.
    Args:
        data: A dictionary containing the data to be encoded in the token.
    Returns:
        A tuple containing the refresh token, its unique identifier, and expiration time, or None if token creation fails.
    """

    try:
        to_encode = data.copy()
        expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
        jti = str(uuid.uuid4())

        to_encode.update({"exp": expire, "type": "refresh", "jti": jti})
        token = jwt.encode(to_encode, settings.refresh_secret_key, algorithm=settings.algorithm)
        return token, jti, expire
    except JWTError:
        return None


def verify_access_token(token: str) -> dict[str, Any] | None:
    """Verify an access token and return its payload.
    Args:
        token: The access token to verify.
    Returns:
        A dictionary containing the token payload, or None if the token is invalid.
    """

    try:
        payload = jwt.decode(token, settings.access_secret_key, algorithms=[settings.algorithm])

        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def verify_refresh_token(token: str) -> dict[str, Any] | None:
    """Verify a refresh token and return its payload.
    Args:
        token: The refresh token to verify.
    Returns:
        A dictionary containing the token payload, or None if the token is invalid.
    """

    try:
        payload = jwt.decode(token, settings.refresh_secret_key, algorithms=[settings.algorithm])

        if payload.get("type") != "refresh":
            return None
        return payload
    except JWTError:
        return None


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Retrieve the current user based on the JWT token in the request. This function extracts the user information from the JWT token payload, verifies its validity, and fetches the corresponding user from the database. If the token is missing, invalid, or if the user cannot be found, appropriate exceptions are raised with detailed error messages.
    Args:
        request: The incoming HTTP request containing the JWT token in its state.
        db: An instance of AsyncSession for interacting with the database.
    Returns:
        A dictionary containing the current user's information.
    """

    payload = getattr(request.state, "user", None)

    if not payload:
        raise UnauthorizedException(detail="Unauthorized")

    user_id = payload.get("user_id")
    email = payload.get("sub")

    if not user_id or not email:
        raise UnauthorizedException(detail="Invalid token payload")

    user = await get_data_by_id(User, user_id, db)

    if not user:
        raise NotFoundException(detail="User not found")

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
    }
