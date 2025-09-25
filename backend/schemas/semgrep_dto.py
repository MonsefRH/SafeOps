from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class SemgrepFinding(BaseModel):
    check_id: Optional[str]
    message: Optional[str]
    file_path: Optional[str]
    file_line_range: List[int]
    severity: str
    code: Optional[str]
    suggestion: Optional[str]

class SemgrepResult(BaseModel):
    failed_checks: List[SemgrepFinding]
    summary: Dict[str, int]

class SemgrepResponse(BaseModel):
    scan_id: int
    status: str
    results: SemgrepResult

class SemgrepErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None