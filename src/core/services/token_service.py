from datetime import datetime
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.config.settings import settings
from src.core.security.jwt_handler import create_access_token, verify_refresh_token
from src.data.models.token_model import RefreshToken

async def save_refresh_token(user_id: int, jti: str, expires_at, db: AsyncSession):
    token = RefreshToken(
        user_id=user_id,
        jti=jti,
        expires_at=expires_at
    )
    db.add(token)
    await db.commit()
    await db.refresh(token)

async def revoke_refresh_token(jti: str, db: AsyncSession):
    token = await db.execute(select(RefreshToken).where(RefreshToken.jti==jti)).scalar_one_or_none()
    if token:
        token.is_revoked = True
        await db.commit()

async def is_refresh_token_revoked(jti: str, db: AsyncSession):
    token = await db.execute(select(RefreshToken).where(RefreshToken.jti==jti)).scalar_one_or_none()
    if not token:
        return True
    if token.expires_at < datetime.utcnow():
        token.is_revoked = True
        await db.commit()
        return True
    return token.is_revoked

async def refresh_access_token(request: Request, db: AsyncSession):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    
    payload = verify_refresh_token(refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    
    if is_refresh_token_revoked(payload["jti"], db):
        raise HTTPException(status_code=401, detail="Refresh token revoked")
    
    user_id = payload["id"]
    email = payload["sub"]

    data = {"user_id": user_id, "sub": email}
    access_token, _, _ = create_access_token(data)

    response = JSONResponse({"access_token": access_token, "token_type": "bearer"})
    response.set_cookie(key="access_token", value=access_token, httponly=True, samesite="lax", secure=False, max_age=settings.access_token_expire_minutes*60)
    return response