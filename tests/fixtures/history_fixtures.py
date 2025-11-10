from datetime import datetime, timezone

import pytest
from unittest.mock import Mock,patch

@pytest.fixture
def history_mock_session():
    # for the rollback in the exception
    sess= Mock()
    sess.rollback.return_value = None
    with patch('services.history_service.db.session',sess) :
        yield sess

@pytest.fixture
def history_mock_scan_history():
    instance=Mock(
        id=42,
        user_id = 1,
        repo_id=2,
        scan_result={"status":"ok"},
        repo_url="http://github.com/user/repo",
        status="success",
        score=60,
        compliant=True,
        created_at=datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc),
        input_type="repo",
        scan_type="semgrep"
    )
    with patch('services.history_service.ScanHistory') as mock_cls:
        mock_cls.return_value=instance
        yield mock_cls

@pytest.fixture
def history_mock_file_content():
    instance = Mock()
    instance.id = 40
    instance.file_path="Dockerfile"

    mock_query = Mock()
    mock_query.filter_by.return_value.first.return_value = instance

    with patch("services.history_service.FileContent") as mock_cls:
        mock_cls.query = mock_query
        yield mock_cls

@pytest.fixture
def history_mock_query():
    q = Mock()
    q.filter_by.side_effect = lambda **kw: q
    # to keep the chaining and return the same object
    q.order_by.side_effect = lambda _: q
    q.all.return_value = []
    return q