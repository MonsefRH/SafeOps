import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
import os


# Mock Google OAuth environment variables
os.environ["GOOGLE_CLIENT_ID"] = "test-google-client-id"
os.environ["GOOGLE_CLIENT_SECRET"] = "test-google-client-secret"


@pytest.fixture
def google_mock_user():
    """Mock User model for Google authentication."""
    user = Mock()
    user.id = 1
    user.name = "Alice Google"
    user.email = "alice@gmail.com"
    user.password = None
    return user


@pytest.fixture
def google_mock_flow():
    """Mock Google OAuth Flow."""
    with patch("services.google_service.Flow") as mock_flow_cls:
        # Mock flow instance
        flow_instance = MagicMock()

        # Mock credentials
        mock_credentials = Mock()
        mock_credentials.id_token = "mock-id-token-12345"
        flow_instance.credentials = mock_credentials

        # Mock authorization_url method
        flow_instance.authorization_url.return_value = (
            "https://accounts.google.com/o/oauth2/auth"
            "?client_id=test-google-client-id"
            "&scope=openid+https%3A//www.googleapis.com/auth/userinfo.email"
            "+https%3A//www.googleapis.com/auth/userinfo.profile"
            "&redirect_uri=http://localhost:5000/auth/google/callback"
            "&access_type=offline"
            "&prompt=consent",
            "state-string"
        )

        # Mock fetch_token (doesn't need to return anything)
        flow_instance.fetch_token = Mock(return_value=None)

        # from_client_config returns flow instance
        mock_flow_cls.from_client_config.return_value = flow_instance

        yield mock_flow_cls


@pytest.fixture
def google_mock_id_token():
    """Mock Google ID token verification."""
    with patch("services.google_service.id_token") as mock_id_token:
        # Mock verified token data
        mock_id_token.verify_oauth2_token.return_value = {
            "sub": "google-user-id-123",
            "email": "alice@gmail.com",
            "name": "Alice Google",
            "email_verified": True
        }
        yield mock_id_token


@pytest.fixture
def google_mock_db_session(google_mock_user):
    """Mock database session for Google service."""
    sess = Mock()

    # Mock User.query.filter_by(email=...).first()
    user_query = Mock()
    user_query.filter_by = Mock(return_value=user_query)
    user_query.first = Mock(return_value=None)  # Default: new user

    with patch("services.google_service.User") as mock_user_cls:
        # Set up query property
        type(mock_user_cls).query = PropertyMock(return_value=user_query)

        # Mock User constructor
        mock_user_cls.return_value = google_mock_user

        # Mock session methods
        sess.add = Mock()
        sess.commit = Mock()
        sess.rollback = Mock()
        sess.flush = Mock()

        with patch("services.google_service.db.session", sess):
            yield sess


@pytest.fixture
def google_mock_flask_app():
    """Mock Flask app context for JWT token generation (Google)."""
    from flask import Flask
    from flask_jwt_extended import JWTManager

    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "test-jwt-secret"
    JWTManager(app)

    with app.app_context():
        yield app