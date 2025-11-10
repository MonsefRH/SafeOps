from datetime import datetime, timezone

import pytest
from unittest.mock import Mock,patch
from services.history_service import get_scan_history


def test_get_scan_history_no_filter(history_mock_session,history_mock_query,history_mock_file_content):
    # Fake DB rows
    row1 = Mock(
        id=1, user_id=1, repo_id=10, scan_result={"a": 1},
        repo_url="https://gh.com/r1", status="success", score=100,
        compliant=True,
        created_at=datetime(2025, 1, 2, 0, 0, tzinfo=timezone.utc),
        input_type="content", scan_type="t5",
    )
    row2 = Mock(
        id=2, user_id=1, repo_id=None, scan_result={"b": 2},
        repo_url=None, status="failed", score=30,
        compliant=False,
        created_at=datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc),
        input_type=None, scan_type="checkov",
    )

    history_mock_query.all.return_value = [row1, row2]
    with patch("services.history_service.ScanHistory.query", history_mock_query):
        history_mock_query._order_q.all.return_value = [row1, row2]
        history = get_scan_history(user_id=1)
    print(history)
    assert len(history) == 2
    assert history[0]["id"] == 1
    assert history[0]["item_name"] == "Dockerfile 40"
    assert history[1]["id"] == 2
    assert history[1]["item_name"] is None


def test_get_scan_history_with_scan_type(
    history_mock_session,
    history_mock_query,
    history_mock_file_content
):
    rows = [
        Mock(id=3, user_id=1, scan_type="t5"),
        Mock(id=1, user_id=1, scan_type="t5"),
        Mock(id=2, user_id=1, scan_type="checkov"),
    ]
    history_mock_query.all.return_value = [rows[0], rows[1]]

    with patch("services.history_service.ScanHistory.query", history_mock_query):
        history_mock_query.filter_by.return_value.filter_by.return_value.order_by.return_value.all.return_value = [rows[0],
                                                                                                                   rows[2]]
        result = get_scan_history(user_id=1, scan_type="t5")

    assert [h["id"] for h in result] == [3,1]

def test_get_scan_history_missing_user_id(history_mock_session):
    with pytest.raises(ValueError, match="user_id is required"):
        get_scan_history(user_id=None)

def test_get_scan_history_db_error(history_mock_session, history_mock_query):
    history_mock_query.filter_by.side_effect = Exception("DB down")

    with patch("services.history_service.ScanHistory.query", history_mock_query):
        with pytest.raises(RuntimeError, match="Failed to fetch scan history"):
            get_scan_history(user_id=1)

    history_mock_session.rollback.assert_called_once()



def test_history_service_returns_valid_dto(
    history_mock_session,
    history_mock_query,
    history_mock_file_content
):
    row = Mock(
        id=5, user_id=1, repo_id=None, scan_result={"msg": "ok"},
        repo_url=None, status="success", score=88,
        compliant=True,
        created_at=datetime.now(timezone.utc),
        input_type="content", scan_type="t5",
    )
    history_mock_query.all.return_value = [row]

    # No FileContent → item_name = None
    with patch("services.history_service.FileContent.query.filter_by", return_value=Mock(first=lambda: None)):
        with patch("services.history_service.ScanHistory.query", history_mock_query):
            from schemas.history_dto import ScanHistoryResponse

            history = get_scan_history(user_id=1)
            dto = ScanHistoryResponse(**history[0])
            assert dto.id == 5
            assert dto.item_name is None