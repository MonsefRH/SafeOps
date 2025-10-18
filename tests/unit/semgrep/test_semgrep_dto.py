import pytest
from pydantic import ValidationError
from schemas.semgrep_dto import SemgrepFinding, SemgrepResult, SemgrepResponse, SemgrepErrorResponse

def test_semgrep_finding_valid():
    data = {
        "check_id": "rule1",
        "message": "Use secure function",
        "file_path": "/app.py",
        "file_line_range": [10, 12],
        "severity": "HIGH",
        "code": "print(secret)",
        "suggestion": "Use environment variables"
    }
    finding = SemgrepFinding(**data)
    assert finding.check_id == "rule1"
    assert finding.severity == "HIGH"
    assert finding.code == "print(secret)"
    assert finding.suggestion == "Use environment variables"
    assert finding.model_dump() == data

def test_semgrep_finding_invalid_severity():
    data = {
        "check_id": "rule1",
        "message": "Use secure function",
        "file_path": "/app.py",
        "file_line_range": [10, 12],
        "severity": "",
        "code": "print(secret)",
        "suggestion": "Use environment variables"
    }
    with pytest.raises(ValidationError, match="String should have at least 1 character"):
        SemgrepFinding(**data)



def test_semgrep_result_valid():
    finding = SemgrepFinding(
        check_id="rule1",
        message="Use secure function",
        file_path="/app.py",
        file_line_range=[10, 12],
        severity="HIGH",
        code="print(secret)",
        suggestion="Use environment variables"
    )
    result = SemgrepResult(failed_checks=[finding], summary={"failed": 1})
    assert len(result.failed_checks) == 1
    assert result.summary["failed"] == 1

def test_semgrep_response_valid():
    finding = SemgrepFinding(
        check_id="rule1",
        message="Use secure function",
        file_path="/app.py",
        file_line_range=[10, 12],
        severity="HIGH",
        code="print(secret)",
        suggestion="Use environment variables"
    )
    result = SemgrepResult(failed_checks=[finding], summary={"failed": 1})
    response = SemgrepResponse(scan_id=1, status="failed", results=result)
    assert response.scan_id == 1
    assert response.status == "failed"
    assert response.model_dump() == {
        "scan_id": 1,
        "status": "failed",
        "results": {
            "failed_checks": [{
                "check_id": "rule1",
                "message": "Use secure function",
                "file_path": "/app.py",
                "file_line_range": [10, 12],
                "severity": "HIGH",
                "code": "print(secret)",
                "suggestion": "Use environment variables"
            }],
            "summary": {"failed": 1}
        }
    }

def test_semgrep_response_invalid_scan_id():
    finding = SemgrepFinding(
        check_id="rule1",
        message="Use secure function",
        file_path="/app.py",
        file_line_range=[10, 12],
        severity="HIGH",
        code="print(secret)",
        suggestion="Use environment variables"
    )
    result = SemgrepResult(failed_checks=[finding], summary={"failed": 1})
    with pytest.raises(ValueError, match="Scan ID must be greater than 0"):
        SemgrepResponse(scan_id=-1, status="failed", results=result)

def test_semgrep_error_response():
    error = SemgrepErrorResponse(error="Invalid input", details="Missing file")
    assert error.model_dump() == {"error": "Invalid input", "details": "Missing file"}