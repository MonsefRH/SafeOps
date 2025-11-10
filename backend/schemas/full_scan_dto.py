from pydantic import BaseModel, Field
from typing import Dict, Optional, Any

class T5Correction(BaseModel):
    corrected: bool
    content: Optional[str] = None
    error: Optional[str] = None

class FullScanResponse(BaseModel):
    checkov: Dict[str, Any]
    t5: Dict[str, T5Correction]
    checkov_corrected: Dict[str, Any]
    semgrep: Dict[str, Any]

class FullScanRequest(BaseModel):
    repo_url: str=Field(...,min_length=20,description="The full repository URL")

class FullScanErrorResponse(BaseModel):
    error: str