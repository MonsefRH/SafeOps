from pydantic import BaseModel, Field, field_validator
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
    scan_id: int = Field(...,description="The ID of the checkov Response")
    results: CheckovResult

    @field_validator("scan_id")
    @classmethod
    def validate(cls, v) -> int :
        if v <= 0 :
            raise ValueError("Checkov scan id must be greater than 0")
        return v

class CheckovContentRequest(BaseModel):
    content: str = Field(...,min_length=1,description="The content of the checkov scanned file")
    framework: Optional[str] = "terraform"

class CheckovRepoRequest(BaseModel):
    repo_url: str = Field(...,min_length=1, description="The URL of the  repository")

class CheckovErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None