"""This module defines the main application router for the PayU Authentication Service using FastAPI. It includes the necessary imports and sets up the application router by including various route modules such as user management, health checks, and token refresh functionality. Additionally, it defines a startup event handler that initializes the database connection when the application starts. This ensures that the database is ready to handle incoming requests and perform operations as needed throughout the lifecycle of the application. The use of FastAPI's APIRouter allows for modular organization of routes, making it easier to maintain and scale the application as new features are added."""

from fastapi import APIRouter

from src.api.rest.routes.health import health_router
from src.api.rest.routes.refresh import refresh_router
from src.api.rest.routes.user_router import user_router
from src.data.clients.database import engine, init_db
from src.observability.logging.logging_config import logger

app_router = APIRouter()

app_router.include_router(user_router)
app_router.include_router(health_router)
app_router.include_router(refresh_router)


@app_router.on_event("startup")
async def on_start() -> None:
    """Startup event handler for the PayU Authentication Service. This function is executed when the application starts up and is responsible for initializing the database connection and performing any necessary setup tasks. In this implementation, it logs a message indicating that the application has started and then initializes the database by creating the necessary tables and structures if they do not already exist. This ensures that the database is ready to handle incoming requests and perform operations as needed throughout the lifecycle of the application."""
    logger.info("App started...")
    async with engine.begin():
        await init_db()
