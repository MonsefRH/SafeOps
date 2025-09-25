from pydantic import BaseModel
from typing import Optional

class GoogleAuthResponse(BaseModel):
    authorization_url: str

class GoogleCallbackResponse(BaseModel):
    redirect_url: str

class GoogleErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None