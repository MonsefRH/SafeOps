from pydantic import BaseModel
from typing import Optional, List

class RiskSummary(BaseModel):
    name: str
    level: int

class RiskDetail(BaseModel):
    severity: str
    check_id: Optional[str]
    file_path: Optional[str]
    message: Optional[str]
    suggestion: Optional[str]
    scan_type: Optional[str]

class RisksResponse(BaseModel):
    risks: List[RiskSummary]
    details: List[RiskDetail]

class RisksErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None