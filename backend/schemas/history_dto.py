from pydantic import BaseModel, field_validator
from typing import Optional, Dict, Any

class ScanHistoryResponse(BaseModel):
    id: int
    repo_id: Optional[int] = None
    scan_result: Dict[str, Any]
    repo_url: Optional[str] = None
    item_name: Optional[str] = None
    status: Optional[str] = None
    score: Optional[int] = None
    compliant: Optional[bool] = None
    created_at: str
    input_type: Optional[str] = None
    scan_type: Optional[str] = None

    @field_validator('id',mode='before')
    def validate_id(cls, v):
        if v < 0:
            raise ValueError("Id must be positive")
        return v

class HistoryErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None