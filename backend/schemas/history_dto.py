from pydantic import BaseModel
from typing import Optional, Dict, Any

class ScanHistoryResponse(BaseModel):
    id: int
    repo_id: Optional[int]
    scan_result: Dict[str, Any]
    repo_url: Optional[str]
    item_name: Optional[str]
    status: Optional[str]
    score: Optional[int]
    compliant: Optional[bool]
    created_at: str
    input_type: Optional[str]
    scan_type: Optional[str]

class HistoryErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None