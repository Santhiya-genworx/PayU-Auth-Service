from __future__ import annotations

import re

from pydantic import BaseModel, EmailStr, field_validator
from pydantic_settings import SettingsConfigDict


def validate_password_strength(password: str) -> str:
    pattern = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{6,}$")
    if not pattern.match(password):
        raise ValueError(
            "Password must be at least 6 characters long, include one uppercase, one lowercase, one digit, and one special character."
        )
    return password


class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str

    model_config = SettingsConfigDict(from_attributes=True)


class UserRequest(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, password: str) -> str:
        return validate_password_strength(password)


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    is_active: bool

    model_config = SettingsConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, password: str) -> str:
        return validate_password_strength(password)

    model_config = SettingsConfigDict(from_attributes=True)
