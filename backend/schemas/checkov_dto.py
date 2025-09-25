from pydantic import BaseModel
from typing import List, Optional

class CheckovCheck(BaseModel):
    check_id: Optional[str]
    check_name: Optional[str]
    file_path: Optional[str]
    guideline: Optional[str] = None
    file_line_range: Optional[List[int]] = None
    resource: Optional[str] = None
    severity: Optional[str] = None
    suggestion: Optional[str] = None

class CheckovSummary(BaseModel):
    passed: int
    failed: int

class CheckovResult(BaseModel):
    status: str
    path_scanned: Optional[str] = None
    files_found: Optional[List[str]] = None
    passed_checks: List[CheckovCheck]
    failed_checks: List[CheckovCheck]
    summary: CheckovSummary
    score: Optional[int] = None
    compliant: Optional[bool] = None
    stdout: Optional[str] = None
    message: Optional[str] = None

class CheckovResponse(BaseModel):
    scan_id: int
    results: CheckovResult

class CheckovContentRequest(BaseModel):
    content: str
    framework: Optional[str] = "terraform"

class CheckovRepoRequest(BaseModel):
    repo_url: str

class CheckovErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None