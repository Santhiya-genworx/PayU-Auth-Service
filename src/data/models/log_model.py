"""This module defines the SQLAlchemy model for logging API requests and responses in the PayU Authentication Service. The Logs model captures essential information about each API interaction, including the user ID (if available), HTTP method, URL, request body, response body, status code, time taken for the request, and a timestamp of when the log entry was created. The HTTP method is stored as an enumeration to ensure data integrity and facilitate querying based on the method used in API requests. The model also establishes a foreign key relationship with the User model to associate logs with specific users when applicable. By implementing this logging mechanism, we can effectively monitor and analyze API usage patterns, identify potential issues, and maintain a comprehensive record of all interactions with the authentication service."""

from __future__ import annotations

from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.data.clients.database import Base

if TYPE_CHECKING:
    from src.data.models.user_model import User


class Methods(PyEnum):
    """Enumeration of HTTP methods for API requests. This enumeration defines the standard HTTP methods that can be used in API interactions, including GET, POST, PUT, and DELETE. By using an enumeration, we can ensure that only valid HTTP methods are stored in the Logs model, providing better data integrity and making it easier to query logs based on the method used in the request."""

    post = "POST"
    put = "PUT"
    delete = "DELETE"


class Logs(Base):
    """SQLAlchemy model for storing API request and response logs. This model includes fields for capturing the user ID (if available), HTTP method, URL, request body, response body, status code, time taken for the request, and a timestamp of when the log entry was created. The model uses a foreign key relationship to the User model to associate logs with specific users when applicable. The HTTP method is stored as an enumeration to ensure data integrity and facilitate querying based on the method used in API requests."""

    __tablename__ = "logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    method: Mapped[Methods] = mapped_column(Enum(Methods, name="method_enum", create_type=False))
    url: Mapped[str] = mapped_column(String(255), nullable=False)
    request_body: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    response_body: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    status_code: Mapped[int] = mapped_column(nullable=False)
    time_taken: Mapped[float] = mapped_column(Numeric, nullable=False)
    timestamp: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship("User", back_populates="logs")
