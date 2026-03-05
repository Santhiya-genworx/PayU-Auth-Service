from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from src.core.security.hashing import hash_data, verify_data
from src.core.security.jwt_handler import create_access_token, create_refresh_token, verify_refresh_token
from src.data.models.token_model import RefreshToken
from src.data.models.user_model import Role, User
from src.data.repositories.base_repository import get_data_by_any, get_data_by_id, insert_data, update_data_by_any, update_data_by_id
from src.schemas.user_schema import LoginRequest, UserRequest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from src.core.config.settings import settings

async def createUser(user: UserRequest, db: AsyncSession):
    try:
        data = {
            "name": user.name,
            "email": user.email,
            "password": hash_data(user.password),
            "role": Role(user.role)
        }
        await insert_data(User, db, **data)
        return {"message": "User created successfully"}
    except SQLAlchemyError as err:
        raise HTTPException(status_code=500, detail=str(err))

async def login(request: LoginRequest, db: AsyncSession):
    try:
        data = {
            "email": request.email
        }
        user = await get_data_by_any(User, db, **data)

        if not user or not verify_data(request.password,user.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        data = {"sub": user.email, "user_id": user.id}
        access_token, _, _ = create_access_token(data)
        refresh_token, refresh_jti, refresh_expire = create_refresh_token(data)

        data = {
            "user_id": user.id,
            "jti": refresh_jti,
            "expires_at": refresh_expire
        }
        await insert_data(RefreshToken, db, **data)
        data = {"is_active": True}
        await update_data_by_id(User, user.id, db, **data)
        user = await get_data_by_id(User, user.id, db)
        data = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role.value
        }

        response = JSONResponse({"message":"Login successful", "access_token": access_token, "refresh_token": refresh_token, "token_type":"bearer", "user": {**data}})
        response.set_cookie(key="access_token", value=access_token, httponly=True, samesite="lax", secure=False, max_age=settings.access_token_expire_minutes*60)
        response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, samesite="lax", secure=False, max_age=settings.refresh_token_expire_days*24*60*60)
        return response
        
    except SQLAlchemyError as err:
        raise HTTPException(status_code=500, detail=str(err))
    
async def logout(request: Request, db: AsyncSession):
    try:
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            raise HTTPException(status_code=400, detail="No user found")
        payload = verify_refresh_token(refresh_token)
        user_id = payload["user_id"]

        data = {"jti": payload["jti"]}
        values = {"is_revoked": True}
        await update_data_by_any(RefreshToken, db, data, **values)
        data = {"is_active": False}
        await update_data_by_id(User, user_id, db, **data)

        response = JSONResponse({"message":"User logout successful"})
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")

        return response
    except SQLAlchemyError as err:
        raise HTTPException(status_code=500, detail=str(err))