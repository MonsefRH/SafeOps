import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def t5_mock_user_query():
    """Mock User.query for admin service tests."""
    with patch("services.admin_service.User") as mock_user_class:
        mock_query = Mock()
        mock_user_class.query = mock_query
        yield mock_query

@pytest.fixture
def mock_scan_query():
    """Mock ScanHistory.query for admin service tests."""
    with patch("services.admin_service.ScanHistory") as mock_scan_class:
        mock_query = Mock()
        mock_scan_class.query = mock_query
        yield mock_query

@pytest.fixture
def mock_users_query():
    """Mock the complex users query with join and count for admin service tests."""
    # Mock the full query chain
    mock_query = Mock()
    mock_result = [
        Mock(id=1, name="User1", email="u1@example.com", role="user", created_at="2023-01-01T00:00:00", scan_count=3),
        Mock(id=2, name="User2", email="u2@example.com", role="user", created_at="2023-01-02T00:00:00", scan_count=0)
    ]
    mock_query.filter_by.return_value.outerjoin.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = mock_result
    yield mock_query

@pytest.fixture
def admin_mock_db_session():
    """Mock db.session for admin service tests."""
    mock_session = Mock()
    mock_session.rollback = Mock()
    mock_session.query.return_value.func = Mock(return_value=Mock(count=Mock(return_value=10)))  # For total_users count
    with patch("services.admin_service.db.session", mock_session):
        yield mock_session

@pytest.fixture
def mock_filter_by_admin(mock_user_query):
    mock_admin = Mock(id=1, role="admin")
    mock_filter_by_admin = Mock()
    mock_filter_by_admin.first.return_value = mock_admin
    yield mock_filter_by_admin
