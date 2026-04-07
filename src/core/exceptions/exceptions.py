"""This module defines custom exception classes for the PayU Authentication Service. These exceptions are designed to provide clear and specific error messages for various error scenarios that may occur during the operation of the authentication service. By creating custom exceptions that inherit from FastAPI's HTTPException, we can easily raise appropriate HTTP status codes and error details in response to different types of errors, such as resource not found, unauthorized access, conflicts, and bad requests. This structured approach to error handling helps improve the maintainability and readability of the code while providing meaningful feedback to clients consuming the API."""

from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base class for all application exceptions."""

    def __init__(self, detail: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        super().__init__(status_code=status_code, detail=detail)


class NotFoundException(AppException):
    """Resource not found."""

    def __init__(self, detail: str = "Resource not found"):
        super().__init__(detail, status.HTTP_404_NOT_FOUND)


class UnauthorizedException(AppException):
    """Authentication/authorization failure."""

    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(detail, status.HTTP_401_UNAUTHORIZED)


class ConflictException(AppException):
    """Conflict error, e.g., duplicate entry."""

    def __init__(self, detail: str = "Conflict"):
        super().__init__(detail, status.HTTP_409_CONFLICT)


class BadRequestException(AppException):
    """Bad request error, e.g., invalid input."""

    def __init__(self, detail: str = "Bad request"):
        super().__init__(detail, status.HTTP_400_BAD_REQUEST)
