"""This module defines the RefreshToken model for the PayU Authentication Service. The RefreshToken model is a SQLAlchemy model that represents the refresh tokens used for authentication in the system. It includes fields for the token's unique identifier (jti), the user ID it is associated with, the expiration time of the token, and a boolean flag indicating whether the token has been revoked. The model also establishes a relationship with the User model to link each refresh token to a specific user. This allows for efficient management of refresh tokens, including revocation and validation during the authentication process. By storing refresh tokens in the database, we can maintain a secure and scalable authentication system that supports token-based authentication and allows for effective session management."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.data.clients.database import Base

if TYPE_CHECKING:
    from src.data.models.user_model import User


class RefreshToken(Base):
    """SQLAlchemy model for storing refresh tokens in the database. This model includes fields for the token's unique identifier (jti), the user ID it is associated with, the expiration time of the token, and a boolean flag indicating whether the token has been revoked. The model establishes a foreign key relationship with the User model to link each refresh token to a specific user. This allows for efficient management of refresh tokens, including revocation and validation during the authentication process. By storing refresh tokens in the database, we can maintain a secure and scalable authentication system that supports token-based authentication and allows for effective session management."""

    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    jti: Mapped[str] = mapped_column(String(255), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped[User] = relationship("User", back_populates="refresh_tokens")
