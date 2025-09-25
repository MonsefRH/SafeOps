from flask import Blueprint, request, jsonify, redirect
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.github_service import github_login, github_callback, get_github_repos, validate_github_token, save_selected_repos, get_repo_configs
from schemas.github_dto import GithubCallbackResponse, GithubRepo, GithubValidateTokenRequest, GithubValidateTokenResponse, GithubSaveReposRequest, GithubSaveReposResponse, GithubRepoConfig, GithubErrorResponse
from pydantic import ValidationError
import logging

github_bp = Blueprint("github", __name__)
logger = logging.getLogger(__name__)

@github_bp.route("/auth/github")
def github_login_route():
    try:
        auth_url = github_login()
        return redirect(auth_url)
    except ValueError as e:
        logger.error(f"GitHub login error: {str(e)}")
        return jsonify(GithubErrorResponse(error=str(e)).dict()), 400

@github_bp.route("/auth/github/callback")
def github_callback_route():
    try:
        code = request.args.get("code")
        frontend_url = github_callback(code)
        return redirect(GithubCallbackResponse(redirect_url=frontend_url).redirect_url)
    except ValueError as e:
        logger.error(f"GitHub callback error: {str(e)}")
        return jsonify(GithubErrorResponse(error=str(e)).dict()), 400
    except RuntimeError as e:
        logger.error(f"Database error in GitHub callback: {str(e)}")
        return jsonify(GithubErrorResponse(error=str(e)).dict()), 500

@github_bp.route("/github/repos", methods=["GET"])
@jwt_required()
def get_github_repos_route():
    try:
        user_id = get_jwt_identity()
        repos = get_github_repos(user_id)
        return jsonify([GithubRepo(**repo).dict() for repo in repos]), 200
    except ValueError as e:
        logger.error(f"Error fetching repos: {str(e)}")
        return jsonify(GithubErrorResponse(error=str(e)).dict()), 404
    except RuntimeError as e:
        logger.error(f"Database error fetching repos: {str(e)}")
        return jsonify(GithubErrorResponse(error=str(e)).dict()), 500

@github_bp.route("/github/validate-token", methods=["POST"])
@jwt_required()
def validate_github_token_route():
    try:
        user_id = get_jwt_identity()
        data = GithubValidateTokenRequest(**request.get_json())
        result = validate_github_token(user_id, data.token, data.selected_repos)
        return jsonify(GithubValidateTokenResponse(**result).dict()), 200
    except ValidationError as e:
        logger.error(f"Invalid input for validate token: {str(e)}")
        return jsonify(GithubErrorResponse(error="Invalid input", details=str(e)).dict()), 400
    except ValueError as e:
        logger.error(f"Error validating token: {str(e)}")
        return jsonify(GithubErrorResponse(error=str(e)).dict()), 400
    except RuntimeError as e:
        logger.error(f"Database error validating token: {str(e)}")
        return jsonify(GithubErrorResponse(error=str(e)).dict()), 500

@github_bp.route("/github/save-repos", methods=["POST"])
@jwt_required()
def save_selected_repos_route():
    try:
        user_id = get_jwt_identity()
        data = GithubSaveReposRequest(**request.get_json())
        # Extract only required fields for the service
        filtered_repos = [
            {
                "full_name": repo.full_name,
                "name": repo.name,
                "html_url": repo.html_url
            }
            for repo in data.selected_repos
        ]
        result = save_selected_repos(user_id, filtered_repos)
        return jsonify(GithubSaveReposResponse(**result).dict()), 200
    except ValidationError as e:
        logger.error(f"Invalid input for save repos: {str(e)}")
        return jsonify(GithubErrorResponse(error="Invalid input", details=str(e)).dict()), 400
    except RuntimeError as e:
        logger.error(f"Database error saving repos: {str(e)}")
        return jsonify(GithubErrorResponse(error=str(e)).dict()), 500

@github_bp.route("/github/repo-configs", methods=["GET"])
@jwt_required()
def get_repo_configs_route():
    try:
        user_id = get_jwt_identity()
        configs = get_repo_configs(user_id)
        return jsonify([GithubRepoConfig(**config).dict() for config in configs]), 200
    except ValueError as e:
        logger.error(f"Error fetching repo configs: {str(e)}")
        return jsonify(GithubErrorResponse(error=str(e)).dict()), 404
    except RuntimeError as e:
        logger.error(f"Server error fetching repo configs: {str(e)}")
        return jsonify(GithubErrorResponse(error=str(e)).dict()), 500