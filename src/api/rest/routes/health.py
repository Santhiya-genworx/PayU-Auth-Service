from fastapi import APIRouter

health_router = APIRouter()


@health_router.get("/health")
def health_check() -> str:
    return "PayU - Auth Service Health check!"
