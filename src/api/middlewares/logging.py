import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from src.data.models.log_model import Logs, Methods
from src.data.repositories.base_repository import insert_data
from src.api.rest.dependencies import AsyncSessionLocal
from jose import JWTError, jwt
from src.core.config.settings import settings

class LoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        public_urls = [
            "/",
            "/docs",
            "/openapi.json"
        ]
        if request.url.path in public_urls:
            return await call_next(request)
        
        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header:
            token = auth_header.split(" ")[1]

        user_id = None
        if token:
            try:
                payload = jwt.decode(token, settings.access_secret_key, algorithms=[settings.algorithm])
                user_id = payload["user_id"]
            except JWTError:
                user_id = None
        
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start

        if request.method in ["POST", "PUT", "DELETE"]:
            async with AsyncSessionLocal() as db:
                data = {
                    "user_id": user_id,
                    "method": Methods(request.method),
                    "url": str(request.url),
                    "status_code": response.status_code,
                    "time_taken": duration
                }
                await insert_data(Logs, db, **data)
        return response