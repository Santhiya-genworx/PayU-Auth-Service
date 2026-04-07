"""This module defines the authentication middleware for the PayU Authentication Service. The AuthMiddleware class is responsible for intercepting incoming HTTP requests and enforcing authentication checks based on the presence and validity of JWT access tokens. The middleware allows certain public URLs to bypass authentication, while protecting other endpoints that require valid tokens. It checks for the token in both the Authorization header and cookies, decodes and verifies the token using the configured secret key and algorithm, and attaches the user information from the token payload to the request state for use in downstream processing. If authentication fails due to a missing, invalid, or expired token, the middleware returns a 401 Unauthorized response with an appropriate error message. This ensures that only authenticated users can access protected resources while still allowing unauthenticated access to public endpoints."""

from fastapi import Request
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from src.config.settings import settings


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for FastAPI. This middleware checks for the presence of a JWT access token in the Authorization header or cookies of incoming requests. It verifies the token's validity and extracts the user information from the token payload, attaching it to the request state for use in downstream route handlers. If the token is missing, invalid, or expired, the middleware returns a 401 Unauthorized response with an appropriate error message. The middleware also allows certain public URLs to bypass authentication checks, enabling unauthenticated access to those endpoints while securing others that require authentication."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process incoming requests and enforce authentication where necessary. This method checks if the request URL is in the list of public URLs that do not require authentication. If the URL is protected, it looks for a JWT access token in the Authorization header or cookies. If a token is found, it attempts to decode and verify the token using the configured secret key and algorithm. If the token is valid, the user information from the token payload is attached to the request state for use in downstream processing. If the token is missing, invalid, or expired, a 401 Unauthorized response is returned with an appropriate error message. Finally, if authentication checks pass or are bypassed for public URLs, the request is forwarded to the next middleware or route handler in the processing chain.        Args:    request: The incoming HTTP request to be processed.    call_next: A function that takes a Request and returns a Response, used to forward the request to the next middleware or route handler after processing.    Returns:    A Response object resulting from either an authentication failure (401 Unauthorized) or successful forwarding of the request to the next handler."""
        public_urls = ["/", "/docs", "/openapi.json", "/health", "/users/login", "/users/create"]

        if request.url.path in public_urls:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        token = None

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        elif request.cookies.get("access_token"):
            token = request.cookies.get("access_token")

        if not token:
            return JSONResponse(status_code=401, content={"detail": "Token missing"})

        try:
            payload = jwt.decode(
                token,
                settings.access_secret_key,
                algorithms=[settings.algorithm],
            )
            request.state.user = payload

        except JWTError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token"},
            )

        return await call_next(request)
