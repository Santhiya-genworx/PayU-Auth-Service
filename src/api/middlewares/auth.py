from fastapi import Request
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from src.core.config.settings import settings


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
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
