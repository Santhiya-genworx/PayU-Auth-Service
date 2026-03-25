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
    logger.info("App started...")
    async with engine.begin():
        await init_db()
