from pydantic import BaseModel, Field
from typing import Optional

class T5Request(BaseModel):
    dockerfile: str = Field(...,min_length=1,description='Dockerfile')

class T5Response(BaseModel):
    scan_id: int = Field(...,gt=0,description='scan id')
    correction: str
    explanation: str

class T5ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None