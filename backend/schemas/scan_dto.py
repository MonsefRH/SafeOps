from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ScanRequest(BaseModel):
    repo_url: str

class ScanResponse(BaseModel):
    scan_id: int
    status: str
    exit_code: int
    findings: List[Dict[str, Any]]

class ScanErrorResponse(BaseModel):
    status: str = "failed"
    error: str
    details: Optional[str] = None