"""This module defines the user-related routes for the PayU Authentication Service using FastAPI. It includes endpoints for creating a new user, logging in, logging out, and retrieving the current user's profile information. Each endpoint interacts with the database through asynchronous sessions and utilizes the core services defined in the application to perform the necessary operations. The routes are organized under the "/users" prefix, making it easy to manage user-related functionality within the application. By including these routes in the main application router, we can ensure that user management features are accessible and properly integrated into the overall authentication service."""

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
    """Endpoint to create a new user in the PayU Authentication Service. This endpoint accepts a POST request with user data and creates a new user in the database. Returns:    A dictionary containing the result of the user creation operation."""
    return await createUser(user, db)


@user_router.put("/login")
async def user_login(
    user: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Endpoint to log in a user in the PayU Authentication Service. This endpoint accepts a PUT request with user credentials and attempts to authenticate the user. If the credentials are valid, it generates an access token and a refresh token, which are returned in the response. If the credentials are invalid, it returns an appropriate error response. Returns:    A JSON response containing the access token and refresh token if authentication is successful, or an error message if authentication fails."""
    return await login(user, db)


@user_router.put("/logout")
async def user_logout(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Endpoint to log out a user in the PayU Authentication Service. This endpoint accepts a PUT request and requires the user to be authenticated. It invalidates the user's current access token and refresh token, effectively logging the user out of the service. Returns:    A JSON response indicating that the logout operation was successful or an error message if the logout process fails."""
    return await logout(request, db)


@user_router.get("/me")
async def get_me(
    current_user: dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Endpoint to retrieve the current user's profile information in the PayU Authentication Service. This endpoint accepts a GET request and requires the user to be authenticated. It retrieves the user's profile information from the database based on the current user's ID and returns it in the response. Returns:    A dictionary containing the current user's profile information, or an error message if the user is not authenticated or if there is an issue retrieving the profile."""
    return await getProfile(current_user["id"], db)
