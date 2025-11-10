from schemas.github_dto import (
    GithubRepo, GithubCallbackResponse, GithubValidateTokenRequest,
    GithubValidateTokenResponse, GithubSaveReposRequest, GithubSaveReposResponse,
    GithubRepoConfig, GithubErrorResponse
)


def test_github_repo():
    repo = GithubRepo(
        name="repo",
        full_name="user/repo",
        description="Test",
        html_url="https://github.com/user/repo"
    )
    assert repo.is_selected is False


def test_github_callback_response():
    resp = GithubCallbackResponse(redirect_url="http://localhost:3000/callback?token=abc")
    assert resp.redirect_url.startswith("http://localhost:3000")


def test_github_validate_token_request():
    req = GithubValidateTokenRequest(token="abc", selected_repos=["user/repo"])
    assert req.token == "abc"
    assert req.selected_repos == ["user/repo"]


def test_github_save_repos_request():
    req = GithubSaveReposRequest(selected_repos=[
        {"full_name": "a/b", "name": "b", "html_url": "https://github.com/a/b"}
    ])
    assert len(req.selected_repos) == 1


def test_github_error_response():
    err = GithubErrorResponse(error="Invalid", details="Token expired")
    assert err.error == "Invalid"
    assert err.details == "Token expired"