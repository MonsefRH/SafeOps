from unittest.mock import Mock
import pytest
from services.dashboard_service import get_user_stats

def test_get_user_stats_happy_path(
    dashboard_mock_db_session,
    dashboard_mock_scan_history,
):
    dashboard_mock_scan_history.query.filter_by.return_value.count.return_value = 5
    dashboard_mock_scan_history.scan_result = {
        "results": {"summary": {"failed": 8, "passed": 42}, "score": 91.6}
    }

    mock_failed = Mock()
    mock_failed.scalar.return_value = 8
    mock_passed = Mock()
    mock_passed.scalar.return_value = 42
    mock_score = Mock()
    mock_score.scalar.return_value = 91.6

    dashboard_mock_db_session.query.return_value.filter_by.side_effect = [
        mock_failed,
        mock_passed,
        mock_score,
    ]
    stats = get_user_stats(user_id=7)

    assert stats == {
        "policies": 5,
        "alerts": 8,
        "security_score": 92,
    }

    assert dashboard_mock_db_session.query.call_count == 3
    assert dashboard_mock_db_session.rollback.call_count == 0

def test_get_user_stats_no_scans(
    dashboard_mock_db_session,
    dashboard_mock_scan_history,

):
    dashboard_mock_scan_history.query.filter_by.return_value.count.return_value = 0
    dashboard_mock_scan_history.scan_result = {
        "results": {"summary": {"failed": 0, "passed": 0}, "score": 0}
    }

    mock_q = Mock()
    mock_q.scalar.return_value = None
    dashboard_mock_db_session.query.return_value.filter_by.return_value = mock_q

    stats = get_user_stats(user_id=99)

    assert stats == {
        "policies": 0,
        "alerts": 0,
        "security_score": 0,
    }



def test_get_user_stats_db_error(
    dashboard_mock_db_session,
    dashboard_mock_scan_history,

):
    dashboard_mock_scan_history.query.filter_by.side_effect = Exception("DB down")

    with pytest.raises(RuntimeError, match="Failed to fetch stats"):
        get_user_stats(user_id=1)

    dashboard_mock_db_session.rollback.assert_called_once()