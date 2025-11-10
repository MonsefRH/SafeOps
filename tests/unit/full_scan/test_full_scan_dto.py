import pytest
from pydantic import ValidationError
from schemas.full_scan_dto import T5Correction, FullScanResponse, FullScanRequest, FullScanErrorResponse

def test_t5_correction_valid():
    data = {"corrected": True, "content": "fixed", "error": None}
    corr = T5Correction(**data)
    assert corr.corrected is True
    assert corr.content == "fixed"

def test_full_scan_request_valid():
    req = FullScanRequest(repo_url="https://github.com/user/repo")
    assert req.repo_url == "https://github.com/user/repo"

def test_full_scan_request_invalid():
    with pytest.raises(ValidationError):
        FullScanRequest(repo_url="")

def test_full_scan_error():
    err = FullScanErrorResponse(error="boom")
    assert err.error == "boom"