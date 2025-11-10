import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
import os

# Mock environment
os.environ["GITHUB_CLIENT_ID"] = "test-client-id"
os.environ["GITHUB_CLIENT_SECRET"] = "test-client-secret"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret"


@pytest.fixture
def github_mock_user():
    user = Mock()
    user.id = 1
    user.name = "Alice"
    user.email = "alice@example.com"
    user.password = None
    return user


@pytest.fixture
def github_mock_github_user():
    gh = Mock()
    gh.user_id = 1
    gh.github_id = "123456"
    gh.access_token = "gho_valid_token"
    return gh


@pytest.fixture
def github_mock_selected_repo():
    repo = Mock()
    repo.id = 10
    repo.user_id = 1
    repo.full_name = "user/repo"
    repo.name = "repo"
    repo.html_url = "https://github.com/user/repo"
    return repo


@pytest.fixture
def github_mock_repo_config():
    cfg = Mock()
    cfg.id = 100
    cfg.repo_id = 10
    cfg.file_path = "Dockerfile"
    cfg.file_name = "Dockerfile"
    cfg.content = b"FROM python:3.9"
    cfg.sha = "abc123"
    cfg.framework = "dockerfile"
    cfg.full_name = "user/repo"
    cfg.html_url = "https://github.com/user/repo"
    return cfg


@pytest.fixture
def github_mock_db_session(github_mock_user, github_mock_github_user, github_mock_selected_repo, github_mock_repo_config):
    """Mock database session with proper query chains."""
    sess = Mock()

    # Mock User.query.filter_by(email=...).first()
    user_query = Mock()
    user_query.filter_by = Mock(return_value=user_query)
    user_query.first = Mock(return_value=None)  # Default: user doesn't exist

    # Mock GithubUser.query.filter_by(...).first()
    github_query = Mock()
    github_query.filter_by = Mock(return_value=github_query)
    github_query.first = Mock(return_value=github_mock_github_user)

    # Mock SelectedRepo.query.filter_by(...).all()
    selected_repo_query = Mock()
    selected_repo_query.filter_by = Mock(return_value=selected_repo_query)
    selected_repo_query.all = Mock(return_value=[github_mock_selected_repo])
    selected_repo_query.delete = Mock(return_value=None)

    # Patch model queries
    with patch("services.github_service.User") as github_mock_user_cls, \
            patch("services.github_service.GithubUser") as github_mock_github_cls, \
            patch("services.github_service.SelectedRepo") as github_mock_selected_cls, \
            patch("services.github_service.RepoConfig") as github_mock_config_cls:
        # Set up query properties
        type(github_mock_user_cls).query = PropertyMock(return_value=user_query)
        type(github_mock_github_cls).query = PropertyMock(return_value=github_query)
        type(github_mock_selected_cls).query = PropertyMock(return_value=selected_repo_query)

        # Mock RepoConfig query (complex join)
        config_query = Mock()
        config_query.join = Mock(return_value=config_query)
        config_query.filter = Mock(return_value=config_query)
        config_query.all = Mock(return_value=[github_mock_repo_config])
        type(github_mock_config_cls).query = PropertyMock(return_value=config_query)

        # Mock constructors
        github_mock_user_cls.return_value = github_mock_user
        github_mock_github_cls.return_value = github_mock_github_user
        github_mock_selected_cls.return_value = github_mock_selected_repo
        github_mock_config_cls.return_value = github_mock_repo_config

        # Mock session methods
        sess.add = Mock()
        sess.commit = Mock()
        sess.rollback = Mock()
        sess.flush = Mock()
        sess.merge = Mock(return_value=github_mock_repo_config)
        sess.query = Mock(return_value=config_query)

        with patch("services.github_service.db.session", sess):
            yield sess


@pytest.fixture
def github_mock_requests():
    """Mock requests module for API calls."""
    with patch("services.github_service.requests") as mock:
        # Default responses
        github_mock_response = Mock()
        github_mock_response.status_code = 200
        github_mock_response.json = Mock(return_value={})
        github_mock_response.text = ""

        mock.post = Mock(return_value=github_mock_response)
        mock.get = Mock(return_value=github_mock_response)

        yield mock


@pytest.fixture
def github_mock_flask_app():
    """Mock Flask app context for JWT token generation."""
    from flask import Flask
    from flask_jwt_extended import JWTManager

    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "test-jwt-secret"
    JWTManager(app)

    with app.app_context():
        yield app