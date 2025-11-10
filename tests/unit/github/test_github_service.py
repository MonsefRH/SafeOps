import pytest
from unittest.mock import Mock, patch
import base64
from services.github_service import (
    github_login, github_callback, get_github_repos,
    validate_github_token, save_selected_repos, get_repo_configs
)


def test_github_login():
    """Test GitHub OAuth URL generation."""
    url = github_login()
    assert "client_id=test-client-id" in url
    assert "scope=repo user:email" in url
    assert "redirect_uri=http://localhost:5000/auth/github/callback" in url


def test_github_callback_success(github_mock_db_session, github_mock_requests, github_mock_user, github_mock_flask_app):
    """Test successful GitHub OAuth callback."""
    # Setup mock responses
    github_mock_requests.post.return_value.json.return_value = {
        "access_token": "gho_valid_token"
    }

    # Mock multiple GET requests (user info, emails)
    user_response = Mock()
    user_response.json.return_value = {
        "id": 123456,
        "login": "alice",
        "name": "Alice"
    }

    email_response = Mock()
    email_response.json.return_value = [
        {"email": "alice@example.com", "primary": True, "verified": True}
    ]

    github_mock_requests.get.side_effect = [user_response, email_response]

    # Execute
    result = github_callback("code123")

    # Assertions
    assert "access_token=" in result
    assert "refresh_token=" in result
    assert "user_id=1" in result
    assert "name=Alice" in result
    assert "email=alice@example.com" in result
    assert "needs_password=true" in result

    # Verify database operations
    github_mock_db_session.add.assert_called()
    github_mock_db_session.commit.assert_called()


def test_github_callback_missing_code():
    """Test GitHub callback with missing code."""
    with pytest.raises(ValueError, match="Code d'autorisation manquant"):
        github_callback("")


def test_github_callback_no_verified_email(github_mock_db_session, github_mock_requests):
    """Test GitHub callback with unverified email."""
    github_mock_requests.post.return_value.json.return_value = {
        "access_token": "gho_valid_token"
    }

    user_response = Mock()
    user_response.json.return_value = {"id": 123456, "login": "alice"}

    email_response = Mock()
    email_response.json.return_value = [
        {"email": "unverified@example.com", "primary": True, "verified": False}
    ]

    github_mock_requests.get.side_effect = [user_response, email_response]

    with pytest.raises(ValueError, match="Erreur d'authentification"):
        github_callback("code")


def test_get_github_repos(github_mock_db_session, github_mock_requests, github_mock_github_user, github_mock_selected_repo):
    """Test fetching GitHub repositories."""
    # Mock API response
    github_mock_response = Mock()
    github_mock_response.status_code = 200
    github_mock_response.json.return_value = [
        {
            "name": "repo",
            "full_name": "user/repo",
            "description": "Test repo",
            "html_url": "https://github.com/user/repo"
        }
    ]
    github_mock_requests.get.return_value = github_mock_response

    # Execute
    repos = get_github_repos(1)

    # Assertions
    assert len(repos) == 1
    assert repos[0]["full_name"] == "user/repo"
    assert repos[0]["is_selected"] is True


def test_get_github_repos_no_github_account(github_mock_db_session):
    """Test fetching repos without linked GitHub account."""
    # Mock no GitHub user
    with patch("services.github_service.GithubUser") as github_mock_gh:
        github_mock_gh.query.filter_by.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Compte GitHub non lié"):
            get_github_repos(1)


def test_validate_github_token(github_mock_db_session, github_mock_requests, github_mock_flask_app):
    """Test GitHub token validation."""
    user_response = Mock()
    user_response.status_code = 200
    user_response.json.return_value = {"id": 123456}

    repos_response = Mock()
    repos_response.status_code = 200
    repos_response.json.return_value = [
        {
            "name": "repo",
            "full_name": "alice/repo",
            "description": "Test",
            "html_url": "https://github.com/alice/repo"
        }
    ]

    github_mock_requests.get.side_effect = [user_response, repos_response]

    result = validate_github_token(1, "valid-token")

    assert result["message"] == "Jeton validé"
    assert len(result["repos"]) == 1
    assert result["repos"][0]["full_name"] == "alice/repo"


def test_validate_github_token_invalid(github_mock_requests):
    """Test validation with invalid token."""
    github_mock_response = Mock()
    github_mock_response.status_code = 401
    github_mock_requests.get.return_value = github_mock_response

    with pytest.raises(ValueError, match="Jeton invalide"):
        validate_github_token(1, "invalid-token")


def test_save_selected_repos(github_mock_db_session, github_mock_selected_repo):
    """Test saving selected repositories."""
    repos = [
        {"full_name": "alice/repo1", "name": "repo1", "html_url": "https://github.com/alice/repo1"},
        {"full_name": "alice/repo2", "name": "repo2", "html_url": "https://github.com/alice/repo2"}
    ]

    result = save_selected_repos(1, repos)

    assert result["message"] == "Dépôts enregistrés"
    # Verify delete was called to clear existing selections
    assert github_mock_db_session.add.call_count == 2
    github_mock_db_session.commit.assert_called()


def test_get_repo_configs(github_mock_db_session, github_mock_requests, github_mock_github_user, github_mock_selected_repo, github_mock_repo_config):
    """Test fetching repository configuration files."""
    # Mock GitHub API responses
    contents_response = Mock()
    contents_response.status_code = 200
    contents_response.json.return_value = [
        {
            "type": "file",
            "name": "Dockerfile",
            "path": "Dockerfile",
            "url": "https://api.github.com/repos/user/repo/contents/Dockerfile"
        }
    ]

    file_response = Mock()
    file_response.status_code = 200
    # Base64 encode "FROM python:3.9"
    content_b64 = base64.b64encode(b"FROM python:3.9").decode()
    file_response.json.return_value = {
        "content": content_b64,
        "sha": "abc123"
    }

    github_mock_requests.get.side_effect = [contents_response, file_response]

    # Execute
    configs = get_repo_configs(1)

    # Assertions
    assert len(configs) == 1
    assert configs[0]["file_name"] == "Dockerfile"
    assert "FROM python:3.9" in configs[0]["content"]
    assert configs[0]["framework"] == "dockerfile"
    assert configs[0]["repo_full_name"] == "user/repo"


def test_get_repo_configs_no_github_account(github_mock_db_session):
    """Test fetching configs without linked GitHub account."""
    with patch("services.github_service.GithubUser") as github_mock_gh:
        github_mock_gh.query.filter_by.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Compte GitHub non lié"):
            get_repo_configs(1)