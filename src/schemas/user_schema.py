"""This module defines the Pydantic schemas for user-related data in the PayU Authentication Service. The schemas include UserBase, UserRequest, UserResponse, and LoginRequest, which represent the structure of user data for various operations such as user creation, retrieval, and login. The UserRequest and LoginRequest schemas include a password field with a custom validator to ensure that the password meets specific strength criteria. By using Pydantic models, we can enforce data validation and serialization for user-related operations in a consistent and efficient manner throughout the authentication service."""

from __future__ import annotations

import re

from pydantic import BaseModel, EmailStr, field_validator
from pydantic_settings import SettingsConfigDict


def validate_password_strength(password: str) -> str:
    """Validate the strength of a password. This function checks if the provided password meets specific strength criteria, including being at least 6 characters long and containing at least one uppercase letter, one lowercase letter, one digit, and one special character. If the password does not meet these criteria, it raises a ValueError with a descriptive message indicating the requirements for a valid password. By enforcing strong password policies, we can enhance the security of user accounts and protect against common password-related vulnerabilities.    Args:    password: The password string to be validated.    Returns:   The original password string if it meets the strength criteria.    Raises:    ValueError: If the password does not meet the specified strength requirements."""
    pattern = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{6,}$")
    if not pattern.match(password):
        raise ValueError(
            "Password must be at least 6 characters long, include one uppercase, one lowercase, one digit, and one special character."
        )
    return password


class UserBase(BaseModel):
    """Base schema for user-related data. This schema includes common fields for user information such as name, email, and role. It serves as a base class for other user-related schemas, allowing for code reuse and consistent data structure across different operations involving user data. The email field is validated to ensure it is in a proper email format, and the role field can be used to differentiate between different types of users (e.g., admin, regular user). By defining this base schema, we can maintain a clear and organized structure for user data throughout the authentication service."""

    name: str
    email: EmailStr
    role: str

    model_config = SettingsConfigDict(from_attributes=True)


class UserRequest(UserBase):
    """Schema for user creation and update requests. This schema extends the UserBase schema by adding a password field, which is required for creating new users or updating existing users' passwords. The password field includes a custom validator to ensure that the provided password meets specific strength criteria, such as being at least 6 characters long and containing a mix of uppercase letters, lowercase letters, digits, and special characters. By using this schema for user-related requests, we can enforce data validation and ensure that all necessary information is provided when creating or updating user accounts in the authentication service."""

    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, password: str) -> str:
        return validate_password_strength(password)


class UserResponse(BaseModel):
    """Schema for user response data. This schema represents the structure of user data that will be returned in API responses when retrieving user information. It includes fields such as id, name, email, role, and is_active status. By defining this schema, we can ensure that the API responses for user-related endpoints are consistent and contain the necessary information about users while excluding sensitive data such as passwords. This schema can be used to serialize user data before sending it in API responses, providing a clear and organized format for clients consuming the authentication service."""

    id: int
    name: str
    email: EmailStr
    role: str
    is_active: bool

    model_config = SettingsConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    """Schema for user login requests. This schema includes fields for email and password, which are required for authenticating users when they attempt to log in to the authentication service. The email field is validated to ensure it is in a proper email format, and the password field includes a custom validator to enforce password strength criteria. By using this schema for login requests, we can ensure that the necessary information is provided for user authentication while also enforcing security best practices for password strength. This schema can be used to validate incoming login data before processing authentication logic in the service."""

    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, password: str) -> str:
        return validate_password_strength(password)

    model_config = SettingsConfigDict(from_attributes=True)
