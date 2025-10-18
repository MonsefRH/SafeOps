import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_db_session():
    """Mock db.session for user service tests."""
    with patch("services.user_service.db.session") as mock_session:
        mock_session.add = Mock()
        mock_session.commit = Mock()
        mock_session.rollback = Mock()
        mock_session.delete = Mock()
        mock_session.flush = Mock()
        yield mock_session

@pytest.fixture
def mock_user_query():
    """Mock User.query for user service tests."""
    with patch("services.user_service.User") as mock_user_class:
        mock_query = Mock()
        mock_user_class.query = mock_query
        yield mock_query

@pytest.fixture
def mock_pending_user_query():
    """Mock PendingUser.query for user service tests."""
    with patch("services.user_service.PendingUser") as mock_pending_class:
        mock_query = Mock()
        mock_pending_class.query = mock_query
        yield mock_query

@pytest.fixture
def mock_bcrypt():
    """Mock bcrypt for user service tests."""
    with patch("services.user_service.bcrypt") as mock_bcrypt:
        mock_bcrypt.generate_password_hash = Mock(return_value=b"hashed_pass")
        mock_bcrypt.check_password_hash = Mock(return_value=True)
        yield mock_bcrypt

@pytest.fixture
def mock_email():
    """Mock email sending for user service tests."""
    with patch("services.user_service.send_verification_email", return_value=True) as mock:
        yield mock

@pytest.fixture
def mock_jwt():
    """Mock JWT functions for user service tests."""
    with patch("services.user_service.create_access_token", return_value="fake_access_token"), \
         patch("services.user_service.create_refresh_token", return_value="fake_refresh_token"):
        yield