import requests
import os
from dotenv import load_dotenv
import base64
from utils.db import db
from models.user import User
from models.github_user import GithubUser
from models.selected_repo import SelectedRepo
from models.repo_config import RepoConfig
from flask_jwt_extended import create_access_token, create_refresh_token
import logging

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

def github_login():
    """Generate GitHub OAuth authorization URL."""
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        logger.error("GitHub client credentials not configured")
        raise ValueError("GitHub client credentials not configured")
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&scope=repo user:email"
        f"&redirect_uri=http://localhost:5000/auth/github/callback"
    )
    return github_auth_url

def github_callback(code):
    """Handle GitHub OAuth callback and create/update user."""
    if not code:
        logger.error("Missing authorization code")
        raise ValueError("Code d'autorisation manquant")

    try:
        token_url = "https://github.com/login/oauth/access_token"
        payload = {
            "client_id": GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "code": code
        }
        headers = {"Accept": "application/json"}
        response = requests.post(token_url, json=payload, headers=headers)
        token_data = response.json()

        if "error" in token_data:
            logger.error(f"GitHub token exchange failed: {token_data['error']}")
            raise ValueError("Échec de l'échange de code")

        access_token = token_data["access_token"]

        user_response = requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_data = user_response.json()

        email_response = requests.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        emails = email_response.json()
        email = next((e["email"] for e in emails if e["primary"] and e["verified"]), None)

        if not email:
            logger.error("No verified email found")
            raise ValueError("Email non vérifié")

        name = user_data.get("name", user_data.get("login", "GitHub User"))
        github_id = str(user_data["id"])

        try:
            # Check if user exists
            user = User.query.filter_by(email=email).first()
            if user:
                user_id = user.id
                needs_password = user.password is None
            else:
                user = User(name=name, email=email)
                db.session.add(user)
                db.session.flush()  # Get user.id before committing
                user_id = user.id
                needs_password = True

            # Check if GitHub user exists
            github_user = GithubUser.query.filter_by(github_id=github_id).first()
            if not github_user:
                github_user = GithubUser(
                    user_id=user_id,
                    github_id=github_id,
                    access_token=access_token
                )
                db.session.add(github_user)

            db.session.commit()

            frontend_url = (
                f"http://localhost:3000/auth/github/callback"
                f"?access_token={create_access_token(identity=str(user_id))}"
                f"&refresh_token={create_refresh_token(identity=str(user_id))}"
                f"&user_id={user_id}"
                f"&name={name}"
                f"&email={email}"
                f"&needs_password={str(needs_password).lower()}"
            )
            return frontend_url

        except Exception as e:
            logger.error(f"Database error during GitHub callback: {str(e)}")
            db.session.rollback()
            raise RuntimeError("Erreur base de données")

    except Exception as e:
        logger.error(f"GitHub OAuth error: {str(e)}")
        raise ValueError("Erreur d'authentification")

def get_github_repos(user_id):
    """Fetch GitHub repositories for a user."""
    github_user = GithubUser.query.filter_by(user_id=user_id).first()
    if not github_user:
        logger.error(f"No GitHub account linked for user_id {user_id}")
        raise ValueError("Compte GitHub non lié")
    access_token = github_user.access_token
    try:

        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get("https://api.github.com/user/repos", headers=headers)
        if response.status_code != 200:
            logger.error(f"GitHub API error: Status {response.status_code}, Response: {response.text}")
            raise ValueError("Échec récupération dépôts")

        repos = response.json()
        repo_data = [
            {
                "name": repo["name"],
                "full_name": repo["full_name"],
                "description": repo.get("description", ""),
                "html_url": repo["html_url"],
                "has_dependabot": False,
                "is_selected": False
            }
            for repo in repos
        ]
        # Check selected repos
        selected = {repo.full_name for repo in SelectedRepo.query.filter_by(user_id=user_id).all()}
        for repo in repo_data:
            repo["is_selected"] = repo["full_name"] in selected
        return repo_data

    except Exception as e:
        logger.error(f"Error fetching GitHub repos for user_id {user_id}: {str(e)}")
        db.session.rollback()
        raise RuntimeError("Erreur base de données")

def validate_github_token(user_id, token, selected_repos=None):
    """Validate a GitHub token and return accessible repositories."""
    if not token:
        logger.error("No token provided")
        raise ValueError("Jeton requis")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("https://api.github.com/user", headers=headers)
    if response.status_code != 200:
        logger.error(f"Invalid GitHub token: Status {response.status_code}")
        raise ValueError("Jeton invalide")

    user_data = response.json()
    github_id = str(user_data["id"])

    repos_response = requests.get("https://api.github.com/user/repos", headers=headers)
    if repos_response.status_code != 200:
        logger.error(f"Failed to fetch repos: Status {repos_response.status_code}")
        raise ValueError("Échec récupération dépôts")

    repos = repos_response.json()
    repo_data = [
        {
            "name": repo["name"],
            "full_name": repo["full_name"],
            "description": repo.get("description", ""),
            "html_url": repo["html_url"]
        }
        for repo in repos
        if not selected_repos or repo["full_name"] in selected_repos
    ]

    try:
        github_user = GithubUser.query.filter_by(user_id=user_id).first()
        if github_user:
            github_user.access_token = token
            github_user.github_id = github_id
        else:
            github_user = GithubUser(
                user_id=user_id,
                github_id=github_id,
                access_token=token
            )
            db.session.add(github_user)
        db.session.commit()
        return {"message": "Jeton validé", "repos": repo_data}
    except Exception as e:
        logger.error(f"Database error during token validation for user_id {user_id}: {str(e)}")
        db.session.rollback()
        raise RuntimeError("Erreur base de données")

def save_selected_repos(user_id, selected_repos):
    """Save selected GitHub repositories for a user."""
    try:
        # Clear existing selections
        SelectedRepo.query.filter_by(user_id=user_id).delete()

        # Insert new selections
        for repo in selected_repos:
            selected_repo = SelectedRepo(
                user_id=user_id,
                full_name=repo["full_name"],
                name=repo["name"],
                html_url=repo["html_url"]
            )
            db.session.add(selected_repo)

        db.session.commit()
        logger.info(f"Saved {len(selected_repos)} repositories for user_id {user_id}")
        return {"message": "Dépôts enregistrés"}
    except Exception as e:
        logger.error(f"Database error saving repos for user_id {user_id}: {str(e)}")
        db.session.rollback()
        raise RuntimeError("Erreur base de données")

def get_repo_configs(user_id):
    """Fetch and store configuration files from selected repositories."""
    github_user = GithubUser.query.filter_by(user_id=user_id).first()
    if not github_user:
        logger.error(f"No GitHub account linked for user_id {user_id}")
        raise ValueError("Compte GitHub non lié")
    try:

        access_token = github_user.access_token

        repos = SelectedRepo.query.filter_by(user_id=user_id).all()
        repos = [{"id": repo.id, "full_name": repo.full_name, "html_url": repo.html_url} for repo in repos]

        headers = {"Authorization": f"Bearer {access_token}"}
        config_files = []

        for repo in repos:
            def fetch_contents(path=""):
                url = f"https://api.github.com/repos/{repo['full_name']}/contents/{path}"
                response = requests.get(url, headers=headers)
                if response.status_code != 200:
                    logger.warning(f"Failed to fetch contents for {repo['full_name']}/{path}: Status {response.status_code}")
                    return []
                contents = response.json()
                files = []
                for item in contents:
                    if item["type"] == "file" and (
                        item["name"].lower() in ["dockerfile", "jenkinsfile", ".gitlab-ci.yml"]
                        or item["name"].lower().endswith((".yml", ".yaml", ".tf"))
                    ):
                        file_response = requests.get(item["url"], headers=headers)
                        if file_response.status_code == 200:
                            file_data = file_response.json()
                            content = base64.b64decode(file_data["content"]).decode("utf-8", errors="ignore")
                            framework = (
                                "dockerfile" if item["name"].lower() == "dockerfile"
                                else "kubernetes" if item["name"].lower().endswith((".yml", ".yaml"))
                                else "terraform" if item["name"].lower().endswith(".tf")
                                else "unknown"
                            )
                            files.append({
                                "repo_id": repo["id"],
                                "file_path": item["path"],
                                "file_name": item["name"],
                                "content": content,
                                "sha": file_data["sha"],
                                "repo_full_name": repo["full_name"],
                                "repo_html_url": repo["html_url"],
                                "framework": framework
                            })
                    elif item["type"] == "dir":
                        files.extend(fetch_contents(item["path"]))
                return files

            repo_configs = fetch_contents()
            config_files.extend(repo_configs)

            for config in repo_configs:
                content_bytes = config["content"].encode("utf-8")
                repo_config = RepoConfig(
                    repo_id=config["repo_id"],
                    file_path=config["file_path"],
                    file_name=config["file_name"],
                    content=content_bytes,
                    sha=config["sha"],
                    framework=config["framework"]
                )
                db.session.merge(repo_config)  # Upsert on file_path, repo_id
            db.session.commit()

        configs = (
            db.session.query(
                RepoConfig.id,
                RepoConfig.file_path,
                RepoConfig.file_name,
                RepoConfig.content,
                RepoConfig.sha,
                SelectedRepo.full_name,
                SelectedRepo.html_url,
                RepoConfig.framework
            )
            .join(SelectedRepo, RepoConfig.repo_id == SelectedRepo.id)
            .filter(SelectedRepo.user_id == user_id)
            .all()
        )
        configs = [
            {
                "id": config.id,
                "file_path": config.file_path,
                "file_name": config.file_name,
                "content": config.content.decode("utf-8", errors="ignore"),
                "sha": config.sha,
                "repo_full_name": config.full_name,
                "repo_html_url": config.html_url,
                "framework": config.framework
            }
            for config in configs
        ]

        return configs

    except Exception as e:
        logger.error(f"Error fetching repo configs for user_id {user_id}: {str(e)}")
        db.session.rollback()
        raise RuntimeError("Erreur serveur")