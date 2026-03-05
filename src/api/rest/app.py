from fastapi import APIRouter
from src.data.clients.database import Base, engine
from src.api.rest.routes.user_router import user_router
from src.api.rest.routes.health import health_router
from src.api.rest.routes.refresh import refresh_router

app_router = APIRouter()

app_router.include_router(user_router)
app_router.include_router(health_router)
app_router.include_router(refresh_router)

@app_router.on_event("startup")
async def on_start():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)