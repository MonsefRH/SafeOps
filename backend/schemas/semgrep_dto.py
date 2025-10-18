from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional

class SemgrepFinding(BaseModel):
    check_id: Optional[str]
    message: Optional[str]
    file_path: Optional[str]
    file_line_range: List[int]
    severity: str = Field(..., min_length=1)
    code: Optional[str]
    suggestion: Optional[str]

class SemgrepResult(BaseModel):
    failed_checks: List[SemgrepFinding]
    summary: Dict[str, int]

class SemgrepResponse(BaseModel):
    scan_id: int
    status: str  = Field(...,min_length=1)
    results: SemgrepResult

    @field_validator('scan_id')
    @classmethod
    def validate(cls, v:int) -> int:
        if v <= 0 :
            raise ValueError("Scan ID must be greater than 0")
        return v

class SemgrepErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None