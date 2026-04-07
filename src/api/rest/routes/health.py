"""This module defines the health check route for the PayU Authentication Service using FastAPI. The health check endpoint is a simple GET request that returns a string message indicating that the service is up and running. This endpoint can be used for monitoring purposes or to provide a quick way to confirm that the service is operational. By including this route in the application, we can easily verify the health status of the service and ensure that it is functioning correctly."""

from fastapi import APIRouter

health_router = APIRouter()


@health_router.get("/health")
def health_check() -> str:
    """Health check endpoint for the PayU Authentication Service. This endpoint can be used to verify that the service is up and running. When accessed, it returns a simple string message indicating that the health check was successful. This can be useful for monitoring purposes or to provide a quick way to confirm that the service is operational. Returns:    A string message indicating the result of the health check."""
    return "PayU - Auth Service Health check!"
