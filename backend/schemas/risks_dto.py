from pydantic import BaseModel, validator, field_validator
from typing import Optional, List

class RiskSummary(BaseModel):
    name: str
    level: int

    @field_validator('level')
    @classmethod
    def validate_level(cls, v: int):
        if v < 0:
            raise ValueError("Risk summary level must be struct greater than zero.")
        return v

class RiskDetail(BaseModel):
    severity: str
    check_id: Optional[str] = None
    file_path: Optional[str] = None
    message: Optional[str] = None
    suggestion: Optional[str] = None
    scan_type: Optional[str] = None

class RisksResponse(BaseModel):
    risks: List[RiskSummary]
    details: List[RiskDetail]

class RisksErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None