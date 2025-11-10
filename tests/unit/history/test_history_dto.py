import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from schemas.history_dto import ScanHistoryResponse,HistoryErrorResponse

def test_scan_history_response_valid():
    data = {
        "id": 1,
        "repo_id": 2,
        "scan_result": {"msg": "ok"},
        "repo_url": "https://gh.com/repo",
        "item_name": "Dockerfile 101",
        "status": "success",
        "score": 60,
        "compliant": True,
        "created_at": "2025-01-01T12:00:00+00:00",
        "input_type": "http://github.com/user/repo",
        "scan_type": "semgrep",
    }
    dto = ScanHistoryResponse(**data)
    assert dto.id == 1
    assert dto.repo_id == 2
    assert dto.item_name == "Dockerfile 101"
    assert isinstance(dto.created_at,str)

def test_scan_history_optional_fields():
    minimal = {
        "id": 2,
        "scan_result": {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    dto = ScanHistoryResponse(**minimal)
    assert dto.repo_id is None
    assert dto.item_name is None

def test_scan_history_invalid():
    with pytest.raises(ValueError,match="Id must be positive") :
        ScanHistoryResponse(id=-1, created_at="2025-01-01T12:00:00+00:00",scan_result={})

def test_history_error_response():
    err1 = HistoryErrorResponse(error="error")
    assert err1.error == "error"
    assert err1.details is None

    err2 = HistoryErrorResponse(error="error", details="details")
    assert err2.error == "error"
    assert err2.details == "details"

