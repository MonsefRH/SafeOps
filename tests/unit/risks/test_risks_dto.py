import pytest
from pydantic import ValidationError
from schemas.risks_dto import RiskSummary, RiskDetail, RisksResponse, RisksErrorResponse

def test_risk_summary_valid():
    """Test valid RiskSummary."""
    data = {"name": "Critical (ERROR)", "level": 50}
    summary = RiskSummary(**data)
    assert summary.name == "Critical (ERROR)"
    assert summary.level == 50

def test_risk_summary_invalid():
    """Test invalid RiskSummary (negative level)."""
    with pytest.raises(ValidationError):
        RiskSummary(name="Critical", level=-10)  # Assuming level >= 0 validator

def test_risk_detail_valid():
    """Test valid RiskDetail."""
    data = {
        "severity": "ERROR",
        "check_id": "SEC001",
        "file_path": "/Dockerfile",
        "message": "Insecure base image",
        "suggestion": "Use alpine",
        "scan_type": "t5"
    }
    detail = RiskDetail(**data)
    assert detail.severity == "ERROR"
    assert detail.check_id == "SEC001"
    assert detail.scan_type == "t5"

def test_risk_detail_optional_fields():
    """Test RiskDetail with optional fields missing."""
    data = {"severity": "WARNING"}
    detail = RiskDetail(**data)
    assert detail.severity == "WARNING"
    assert detail.check_id is None
    assert detail.file_path is None

def test_risks_response_valid():
    """Test valid RisksResponse serialization."""
    summaries = [RiskSummary(name="Critical", level=10), RiskSummary(name="High", level=5)]
    details = [RiskDetail(severity="ERROR", check_id="SEC001")]
    response = RisksResponse(risks=summaries, details=details)
    assert len(response.risks) == 2
    assert len(response.details) == 1
    assert response.model_dump()["risks"][0]["name"] == "Critical"

def test_risks_error_response_valid():
    """Test valid RisksErrorResponse serialization."""
    error = RisksErrorResponse(error="User not found", details="No scans available")
    assert error.model_dump() == {
        "error": "User not found",
        "details": "No scans available"
    }

    # Test without details
    error_no_details = RisksErrorResponse(error="Server error")
    assert error_no_details.model_dump() == {
        "error": "Server error",
        "details": None
    }