"""This module defines the SQLAlchemy model for the User entity in the PayU Authentication Service. The User model represents the structure of the users table in the database, including fields for id, name, email, password, role, is_active status, created_at timestamp, and updated_at timestamp. It also establishes relationships with the Logs and RefreshToken models to allow for easy access to logs and refresh tokens associated with each user. The email field is unique to ensure that no two users can register with the same email address, and the password field is intended to store hashed passwords for security purposes. The role field can be used to differentiate between different types of users (e.g., admin, regular user), and the is_active field indicates whether a user's account is active or not. By defining this model using SQLAlchemy's ORM features, we can easily interact with the users table in the database, perform CRUD operations, and manage relationships with other models such as Logs and RefreshToken. This structured approach allows for efficient data management and retrieval while maintaining data integrity and security best practices."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.data.clients.database import Base
from src.data.models.log_model import Logs
from src.data.models.token_model import RefreshToken


class User(Base):
    """SQLAlchemy model for the User entity. This model defines the structure of the users table in the database, including fields for id, name, email, password, role, is_active status, created_at timestamp, and updated_at timestamp. The model also establishes a relationship with the Logs model to allow for easy access to logs associated with each user. The email field is unique to ensure that no two users can register with the same email address, and the password field is intended to store hashed passwords for security purposes. The role field can be used to differentiate between different types of users (e.g., admin, regular user), and the is_active field indicates whether a user's account is active or not.    By defining this model using SQLAlchemy's ORM features, we can easily interact with the users table in the database, perform CRUD operations, and manage relationships with other models such as Logs and RefreshToken. This structured approach allows for efficient data management and retrieval while maintaining data integrity and security best practices."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, unique=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="False")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    refresh_tokens: Mapped[list[RefreshToken]] = relationship("RefreshToken", back_populates="user")
    logs: Mapped[list[Logs]] = relationship("Logs", back_populates="user")
