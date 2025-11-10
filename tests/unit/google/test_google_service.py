import pytest
from unittest.mock import patch, Mock, PropertyMock
from services.google_service import google_login, google_callback


def test_google_login(google_mock_flow):
    """Test Google OAuth URL generation."""
    url = google_login()

    # Verify URL components
    assert "https://accounts.google.com/o/oauth2/auth" in url
    assert "client_id=test-google-client-id" in url
    assert "scope=openid" in url
    assert "redirect_uri=http://localhost:5000/auth/google/callback" in url
    assert "access_type=offline" in url
    assert "prompt=consent" in url

    # Verify Flow was called correctly
    google_mock_flow.from_client_config.assert_called_once()


def test_google_login_missing_credentials():
    """Raise ValueError if client_id or secret missing."""
    # Mock environment to return None for credentials
    with patch("services.google_service.GOOGLE_CLIENT_ID", None), \
            patch("services.google_service.GOOGLE_CLIENT_SECRET", None):
        with pytest.raises(ValueError, match="Google client credentials not configured"):
            google_login()


def test_google_callback_success(
        google_mock_flow,
        google_mock_id_token,
        google_mock_db_session,
        google_mock_user,
        google_mock_flask_app
):
    """Test successful Google OAuth callback for new user."""
    # User doesn't exist → will be created
    result = google_callback("auth-code-123")

    # Verify URL structure
    assert result.startswith("http://localhost:3000/auth/google/callback")
    assert "access_token=" in result
    assert "refresh_token=" in result
    assert "user_id=1" in result
    assert "alice@gmail.com" in result  # URL encoded email
    assert "needs_password=true" in result

    # Verify database operations
    google_mock_db_session.add.assert_called_once()
    google_mock_db_session.flush.assert_called_once()
    google_mock_db_session.commit.assert_called_once()

    # Verify OAuth flow was executed
    google_mock_flow.from_client_config.assert_called_once()
    flow_instance = google_mock_flow.from_client_config.return_value
    flow_instance.fetch_token.assert_called_once_with(code="auth-code-123")

    # Verify ID token was verified
    google_mock_id_token.verify_oauth2_token.assert_called_once()


def test_google_callback_existing_user(
        google_mock_flow,
        google_mock_id_token,
        google_mock_db_session,
        google_mock_user,
        google_mock_flask_app
):
    """Test Google OAuth callback for existing user with password."""
    # Mock existing user with password
    with patch("services.google_service.User") as mock_user_cls:
        user_query = Mock()
        user_query.filter_by = Mock(return_value=user_query)

        existing_user = Mock()
        existing_user.id = 1
        existing_user.email = "alice@gmail.com"
        existing_user.password = "hashed_password_123"

        user_query.first = Mock(return_value=existing_user)
        type(mock_user_cls).query = PropertyMock(return_value=user_query)

        result = google_callback("auth-code-123")

    # Should indicate password already set
    assert "needs_password=false" in result
    assert "user_id=1" in result

    # Should NOT add new user, only commit
    # (add is only called for new users)
    google_mock_db_session.commit.assert_called()


def test_google_callback_missing_code():
    """Test error when authorization code is missing."""
    with pytest.raises(ValueError, match="Code d'autorisation manquant"):
        google_callback("")


def test_google_callback_no_email(google_mock_flow, google_mock_id_token):
    """Test error when ID token doesn't contain email."""
    # Mock ID token without email
    google_mock_id_token.verify_oauth2_token.return_value = {
        "sub": "google-user-123",
        "name": "No Email User"
        # Missing 'email' field
    }

    with pytest.raises(ValueError, match="Erreur lors de l'authentification"):
        google_callback("code-without-email")


def test_google_callback_db_error(
        google_mock_flow,
        google_mock_id_token,
        google_mock_db_session,
        google_mock_flask_app
):
    """Test error handling when database commit fails."""
    # Simulate database error
    google_mock_db_session.commit.side_effect = Exception("Database connection lost")

    with pytest.raises(ValueError, match="Erreur lors de l'authentification"):
        google_callback("code")

    # Verify rollback was called
    google_mock_db_session.rollback.assert_called_once()