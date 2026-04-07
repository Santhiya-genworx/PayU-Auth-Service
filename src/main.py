"""This module serves as the entry point for the PayU Authentication Service. It sets up the FastAPI application, configures CORS middleware to allow cross-origin requests from specified origins, and includes the authentication middleware to handle authentication for incoming requests. The module also defines a simple welcome endpoint at the root URL ("/") that returns a JSON response with a welcome message, which can be used as a health check or greeting message to confirm that the service is operational. The application is structured to allow for easy expansion with additional routes and middleware as needed for the authentication service's functionality."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.middlewares.auth import AuthMiddleware
from src.api.rest.app import app_router
from src.config.settings import settings

app = FastAPI(title="PayU - Authentication Service", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuthMiddleware)

app.include_router(app_router)


@app.get("/")
def welcome() -> dict[str, str]:
    """Welcome endpoint for the PayU Authentication Service. This endpoint serves as a simple health check or greeting message to confirm that the service is up and running. When accessed, it returns a JSON response with a welcome message. This can be useful for monitoring purposes or to provide a friendly message to users who access the root URL of the service.  Returns:    A dictionary containing a welcome message to indicate that the PayU Authentication Service is operational."""
    return {"message": "Welcome to my website!"}
