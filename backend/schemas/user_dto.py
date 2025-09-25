from pydantic import BaseModel
from typing import Optional

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class VerifyCodeRequest(BaseModel):
    email: str
    code: str

class LoginRequest(BaseModel):
    email: str
    password: str

class SetPasswordRequest(BaseModel):
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
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