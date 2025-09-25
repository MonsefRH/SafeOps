from pydantic import BaseModel
from typing import Optional

class T5Request(BaseModel):
    dockerfile: str

class T5Response(BaseModel):
    scan_id: int
    correction: str
    explanation: str

class T5ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None