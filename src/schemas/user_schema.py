import re
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator

class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str

    class Config:
        from_attributes: True

class UserRequest(UserBase):
    password: str

    @field_validator("password")
    def validate_password(cls, password):
        pattern = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{6,}$")
        if not pattern.match(password):
            raise ValueError("Password must be at least 6 characters long, include one uppercase, one lowercase, one digit, and one special character.")
        return password

class UserResponse(UserRequest):
    id: int
    is_active: bool

    class Config:
        from_attributes: True    

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    def validate_password(cls, password):
        pattern = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{6,}$")
        if not pattern.match(password):
            raise ValueError("Password must be at least 6 characters long, include one uppercase, one lowercase, one digit, and one special character.")
        return password

    class Config:
        from_attributes: True