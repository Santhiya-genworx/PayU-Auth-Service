"""This module defines the token service for the PayU Authentication Service. It provides functions for managing refresh tokens, including saving new refresh tokens to the database, revoking existing tokens, checking if a token has been revoked, and refreshing access tokens using valid refresh tokens. The service interacts with the database using SQLAlchemy's asynchronous session and handles token generation and verification using JWT. It also includes error handling to ensure that any issues during token management are properly reported as application exceptions. This service is a crucial component of the authentication system, enabling secure and efficient management of user sessions through access and refresh tokens."""

from datetime import UTC, datetime

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.core.exceptions.exceptions import AppException, UnauthorizedException
from src.core.security.jwt_handler import create_access_token, verify_refresh_token
from src.data.models.token_model import RefreshToken


async def save_refresh_token(
    user_id: int,
    jti: str,
    expires_at: datetime,
    db: AsyncSession,
) -> None:
    """Save a new refresh token to the database. This function creates a new RefreshToken instance with the provided user ID, JWT ID (jti), and expiration time, and then adds it to the database session. It commits the transaction to persist the token in the database and refreshes the instance to get any updated fields. If any exceptions occur during this process, it raises an AppException with the error details.    Args:
    user_id: The ID of the user associated with the refresh token.    jti: The unique identifier for the JWT token, used to track and manage the token in the database.    expires_at: The expiration time of the refresh token.    db: An instance of AsyncSession for interacting with the database.    Raises:
    AppException: If any error occurs while saving the refresh token to the database, such as database connection issues or transaction failures."""
    try:
        token = RefreshToken(
            user_id=user_id,
            jti=jti,
            expires_at=expires_at,
        )
        db.add(token)
        await db.commit()
        await db.refresh(token)

    except Exception as err:
        raise AppException(detail=str(err)) from err


async def revoke_refresh_token(jti: str, db: AsyncSession) -> None:
    """Revoke an existing refresh token by marking it as revoked in the database. This function retrieves the RefreshToken instance corresponding to the provided JWT ID (jti) from the database. If the token is found, it sets the is_revoked flag to True and commits the transaction to update the token's status in the database. If any exceptions occur during this process, it raises an AppException with the error details.    Args:
    jti: The unique identifier for the JWT token that needs to be revoked.    db: An instance of AsyncSession for interacting with the database.    Raises:
    AppException: If any error occurs while revoking the refresh token in the database, such as database connection issues or transaction failures."""
    try:
        result = await db.execute(select(RefreshToken).where(RefreshToken.jti == jti))
        token: RefreshToken | None = result.scalar_one_or_none()

        if token:
            token.is_revoked = True
            await db.commit()

    except Exception as err:
        raise AppException(detail=str(err)) from err


async def is_refresh_token_revoked(jti: str, db: AsyncSession) -> bool:
    """Check if a refresh token has been revoked. This function retrieves the RefreshToken instance corresponding to the provided JWT ID (jti) from the database. If the token is not found, it returns True, indicating that the token is effectively revoked. If the token is found but has expired, it marks the token as revoked in the database and returns True. If the token is found and is still valid, it returns the value of the is_revoked flag to indicate whether the token has been revoked or not. If any exceptions occur during this process, it raises an AppException with the error details.    Args:
    jti: The unique identifier for the JWT token to check for revocation.    db: An instance of AsyncSession for interacting with the database.    Returns:
    A boolean value indicating whether the refresh token has been revoked (True) or is still valid (False).    Raises:
    AppException: If any error occurs while checking the revocation status of the refresh token in the database, such as database connection issues or transaction failures."""
    try:
        result = await db.execute(select(RefreshToken).where(RefreshToken.jti == jti))
        token: RefreshToken | None = result.scalar_one_or_none()

        if not token:
            return True

        if token.expires_at < datetime.now(UTC):
            token.is_revoked = True
            await db.commit()
            return True

        return token.is_revoked

    except Exception as err:
        raise AppException(detail=str(err)) from err


async def refresh_access_token(
    request: Request,
    db: AsyncSession,
) -> JSONResponse:
    """Refresh an access token using a valid refresh token. This function checks for the presence of a refresh token in the request cookies, verifies its validity, and checks if it has been revoked. If the refresh token is valid and not revoked, it generates a new access token based on the user information contained in the refresh token's payload. The new access token is then returned in a JSON response, and also set as an HTTP-only cookie for client-side storage. If any issues arise during this process, such as a missing, invalid, or revoked refresh token, or if token generation fails, appropriate exceptions are raised with detailed error messages.    Args:
    request: The incoming HTTP request containing the refresh token in its cookies.    db: An instance of AsyncSession for interacting with the database.    Returns:
    A JSONResponse containing the new access token and its type, with the access token also set as an HTTP-only cookie.    Raises:
    UnauthorizedException: If the refresh token is missing, invalid, expired, or revoked.    AppException: If any error occurs during the token refresh process, such as database connection issues or token generation failures."""
    try:
        refresh_token = request.cookies.get("refresh_token")

        if not refresh_token:
            raise UnauthorizedException(detail="Missing refresh token")

        payload = verify_refresh_token(refresh_token)

        if not payload:
            raise UnauthorizedException(detail="Invalid or expired refresh token")

        if await is_refresh_token_revoked(payload["jti"], db):
            raise UnauthorizedException(detail="Refresh token revoked")

        user_id: int = payload["user_id"]
        email: str = payload["sub"]

        data = {"user_id": user_id, "sub": email}
        access = create_access_token(data)

        if not access:
            raise AppException(detail="Token generation failed")

        access_token, _, _ = access

        response = JSONResponse({"access_token": access_token, "token_type": "bearer"})

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            samesite="none",
            secure=True,
            max_age=settings.access_token_expire_minutes * 60,
        )

        return response

    except Exception as err:
        raise AppException(detail=str(err)) from err
