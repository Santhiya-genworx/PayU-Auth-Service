from datetime import UTC, datetime

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config.settings import settings
from src.core.exceptions.exceptions import AppException, UnauthorizedException
from src.core.security.jwt_handler import create_access_token, verify_refresh_token
from src.data.models.token_model import RefreshToken


async def save_refresh_token(
    user_id: int,
    jti: str,
    expires_at: datetime,
    db: AsyncSession,
) -> None:
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
    try:
        result = await db.execute(select(RefreshToken).where(RefreshToken.jti == jti))
        token: RefreshToken | None = result.scalar_one_or_none()

        if token:
            token.is_revoked = True
            await db.commit()

    except Exception as err:
        raise AppException(detail=str(err)) from err


async def is_refresh_token_revoked(jti: str, db: AsyncSession) -> bool:
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
