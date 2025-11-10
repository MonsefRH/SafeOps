import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def dashboard_mock_db_session():
    """Mock Flask-SQLAlchemy session + query builder."""
    mock_session = Mock()
    mock_session.rollback.return_value = None
    with patch("services.dashboard_service.db.session", mock_session):
        yield mock_session

@pytest.fixture
def dashboard_mock_scan_history():
    """Mock the ScanHistory model used in queries."""
    mock_model = Mock()
    with patch("services.dashboard_service.ScanHistory", mock_model):
        yield mock_model
