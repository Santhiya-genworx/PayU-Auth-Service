"""This module defines the route for refreshing access tokens in the PayU Authentication Service using FastAPI. The refresh token endpoint allows clients to obtain a new access token using a valid refresh token. The endpoint accepts a GET request and requires the client to provide a valid refresh token in the request headers. The function verifies the refresh token, and if it is valid, it generates a new access token and returns it in the response. If the refresh token is invalid or expired, it returns an appropriate error response. This endpoint enables clients to maintain authenticated sessions without requiring users to re-authenticate, as long as they have a valid refresh token."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies import get_db
from src.core.services.token_service import refresh_access_token

refresh_router = APIRouter()


@refresh_router.get("/refresh")
async def refresh_token(request: Request, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """Endpoint to refresh an access token using a valid refresh token. This endpoint accepts a GET request and requires the client to provide a valid refresh token in the request headers. The function verifies the refresh token, and if it is valid, it generates a new access token and returns it in the response. If the refresh token is invalid or expired, it returns an appropriate error response. This endpoint allows clients to obtain a new access token without requiring the user to re-authenticate, as long as they have a valid refresh token. Returns:    A JSON response containing the new access token or an error message if the refresh token is invalid."""
    return await refresh_access_token(request, db)
