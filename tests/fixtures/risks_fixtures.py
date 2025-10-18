import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_scan_history_query():
    """Mock ScanHistory.query for risks service tests."""
    with patch("services.risks_service.ScanHistory") as mock_class:
        mock_query = Mock()
        mock_class.query = mock_query
        yield mock_query

@pytest.fixture
def mock_db_session():
    """Mock db.session for risks service tests."""
    mock_session = Mock()
    mock_session.rollback = Mock()
    with patch("services.risks_service.db.session", mock_session):
        yield mock_session