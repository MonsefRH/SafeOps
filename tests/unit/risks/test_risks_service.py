import pytest
from unittest.mock import Mock
from services.risks_service import get_risks


def test_get_risks_valid(mock_scan_history_query):
    """Test successful risk fetching with sample scans."""
    # Mock query to return 2 scans with failed checks
    mock_scan1 = Mock()
    mock_scan1.scan_result = {
        "results": {
            "failed_checks": [
                {"severity": "ERROR", "check_id": "SEC001", "file_path": "/Dockerfile", "message": "Insecure image",
                 "suggestion": "Use alpine"}
            ]
        }
    }
    mock_scan1.scan_type = "t5"

    mock_scan2 = Mock()
    mock_scan2.scan_result = {
        "results": {
            "failed_checks": [
                {"severity": "WARNING", "check_id": "SEC002", "file_path": "/app.py", "message": "Hardcoded secret",
                 "suggestion": "Use env vars"}
            ]
        }
    }
    mock_scan2.scan_type = "static"

    mock_scan_history_query.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
        mock_scan1, mock_scan2]

    result = get_risks(1)

    assert len(result["risks"]) == 3  # ERROR, WARNING, INFO (INFO=0)
    assert result["risks"][0]["name"] == "Critical (ERROR)"
    assert result["risks"][0]["level"] == 10  # 1 ERROR * 10
    assert result["risks"][1]["name"] == "High (WARNING)"
    assert result["risks"][1]["level"] == 5  # 1 WARNING * 5

    assert len(result["details"]) == 2
    assert result["details"][0]["severity"] == "ERROR"
    assert result["details"][0]["check_id"] == "SEC001"
    assert result["details"][1]["severity"] == "WARNING"
    assert result["details"][1]["scan_type"] == "static"


def test_get_risks_no_user_id():
    """Test with missing user_id."""
    with pytest.raises(ValueError, match="user_id is required"):
        get_risks(None)


def test_get_risks_no_scans(mock_scan_history_query):
    """Test with no scans for user."""
    mock_scan_history_query.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = []

    result = get_risks(1)

    assert len(result["risks"]) == 3
    assert all(r["level"] == 0 for r in result["risks"])  # All zero
    assert len(result["details"]) == 0


def test_get_risks_exception(mock_scan_history_query, mock_db_session):
    """Test RuntimeError on query failure."""
    mock_scan_history_query.filter_by.side_effect = Exception("DB query error")

    with pytest.raises(RuntimeError, match="Failed to fetch risks"):
        get_risks(1)

    mock_db_session.rollback.assert_called_once()