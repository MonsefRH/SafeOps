import pytest
from pydantic import ValidationError
from schemas.checkov_dto import CheckovContentRequest, CheckovRepoRequest, CheckovResponse, CheckovCheck, CheckovSummary, CheckovResult, CheckovErrorResponse

def test_checkov_content_request_valid():
    data = {"content": "resource aws_s3_bucket { bucket = 'test' }", "framework": "terraform"}
    req = CheckovContentRequest(**data)
    assert req.content == data["content"]
    assert req.framework == "terraform"

def test_checkov_content_request_invalid():
    with pytest.raises(ValidationError, match="String should have at least 1 character"):
        CheckovContentRequest(content="", framework="terraform")

def test_checkov_repo_request_valid():
    data = {"repo_url": "https://github.com/user/repo"}
    req = CheckovRepoRequest(**data)
    assert req.repo_url == data["repo_url"]

def test_checkov_repo_request_invalid():
    with pytest.raises(ValidationError, match="String should have at least 1 character"):
        CheckovRepoRequest(repo_url="")

def test_checkov_response_valid():
    check = CheckovCheck(check_id="CKV_AWS_1", check_name="S3 Public", file_path="/main.tf")
    summary = CheckovSummary(passed=1, failed=0)
    result = CheckovResult(
        status="success", passed_checks=[check], failed_checks=[], summary=summary, score=100, compliant=True
    )
    response = CheckovResponse(scan_id=1, results=result)
    assert response.scan_id == 1
    assert response.results.status == "success"
    assert response.model_dump() == {
        "scan_id": 1,
        "results": {
            "status": "success",
            "path_scanned": None,
            "files_found": None,
            "passed_checks": [{"check_id": "CKV_AWS_1", "check_name": "S3 Public", "file_path": "/main.tf", "guideline": None, "file_line_range": None, "resource": None, "severity": None, "suggestion": None}],
            "failed_checks": [],
            "summary": {"passed": 1, "failed": 0},
            "score": 100,
            "compliant": True,
            "stdout": None,
            "message": None
        }
    }

def test_checkov_response_invalid_scan_id():
    check = CheckovCheck(check_id="CKV_AWS_1", check_name="S3 Public", file_path="/main.tf")
    summary = CheckovSummary(passed=1, failed=0)
    result = CheckovResult(status="success", passed_checks=[check], failed_checks=[], summary=summary)
    with pytest.raises(ValueError, match="Checkov scan id must be greater than 0"):
        CheckovResponse(scan_id=0, results=result)

def test_checkov_error_response():
    error = CheckovErrorResponse(error="Invalid input", details="Empty content")
    assert error.model_dump() == {"error": "Invalid input", "details": "Empty content"}