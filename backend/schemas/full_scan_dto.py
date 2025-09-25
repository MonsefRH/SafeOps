from pydantic import BaseModel
from typing import Dict, Optional, Any

class T5Correction(BaseModel):
    corrected: bool
    content: Optional[str] = None
    error: Optional[str] = None

class FullScanResponse(BaseModel):
    checkov: Dict[str, Any]  # Includes scan_id and results or error
    t5: Dict[str, T5Correction]
    checkov_corrected: Dict[str, Any]  # Includes scan_id and results or error
    semgrep: Dict[str, Any]  # SemgrepScanResponse or error

class FullScanRequest(BaseModel):
    repo_url: str

class FullScanErrorResponse(BaseModel):
    error: str