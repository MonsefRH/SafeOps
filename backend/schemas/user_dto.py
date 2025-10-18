from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Full name, cannot be empty")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=5, description="Password at least 5 characters")
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():  # Extra check for whitespace-only
            raise ValueError("Name cannot be empty or whitespace-only")
        return v.strip()

class VerifyCodeRequest(BaseModel):
    email: EmailStr = Field(..., description="Valid email address")
    code: str = Field(...,min_length=6,max_length=6, description="Valid code")

class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=5, description="Password at least 5 characters")
class SetPasswordRequest(BaseModel):
    password: str = Field(..., min_length=5, description="Password at least 5 characters")

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr = Field(..., description="Valid email address")
    role: str

class RegisterResponse(BaseModel):
    message: str

class VerifyCodeResponse(BaseModel):
    message: str
    access_token: str
    refresh_token: str
    user: UserResponse

class LoginResponse(BaseModel):
    message: str
    access_token: str
    refresh_token: str
    user: UserResponse

class SetPasswordResponse(BaseModel):
    message: str

class RefreshResponse(BaseModel):
    access_token: str

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None