from flask import Blueprint, request, jsonify, redirect
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from utils.db import db
from models.user import User
from models.github_user import GithubUser
from models.selected_repo import SelectedRepo
from models.repo_config import RepoConfig
import requests
import os
from dotenv import load_dotenv
import base64

load_dotenv()

github_bp = Blueprint("github", __name__)

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

@github_bp.route("/auth/github")
def github_login():
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&scope=repo user:email"
        f"&redirect_uri=http://localhost:5000/auth/github/callback"
    )
    return redirect(github_auth_url)

@github_bp.route("/auth/github/callback")
def github_callback():
    try:
        code = request.args.get("code")
        if not code:
            return jsonify({"error": "Code d'autorisation manquant"}), 400

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
            return jsonify({"error": "Échec de l'échange de code"}), 400

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
            return jsonify({"error": "Email non vérifié"}), 400

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
            return redirect(frontend_url)

        except Exception as e:
            print("❌ Erreur PostgreSQL:", e)
            db.session.rollback()
            return jsonify({"error": "Erreur base de données"}), 500

    except Exception as e:
        print("❌ Erreur GitHub OAuth:", e)
        return jsonify({"error": "Erreur d'authentification"}), 500

@github_bp.route("/github/repos", methods=["GET"])
@jwt_required()
def get_github_repos():
    user_id = get_jwt_identity()
    try:
        github_user = GithubUser.query.filter_by(user_id=user_id).first()
        if not github_user:
            return jsonify({"error": "Compte GitHub non lié"}), 404
        access_token = github_user.access_token

        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get("https://api.github.com/user/repos", headers=headers)
        if response.status_code != 200:
            print(f"❌ GitHub API Error: Status {response.status_code}, Response: {response.text}")
            return jsonify({"error": "Échec récupération dépôts"}), 400

        repos = response.json()
        repo_data = [
            {
                "name": repo["name"],
                "full_name": repo["full_name"],
                "description": repo.get("description", ""),
                "html_url": repo["html_url"],
                "has_dependabot": False
            }
            for repo in repos
        ]
        # Check selected repos
        selected = {repo.full_name for repo in SelectedRepo.query.filter_by(user_id=user_id).all()}
        for repo in repo_data:
            repo["is_selected"] = repo["full_name"] in selected
        return jsonify(repo_data)

    except Exception as e:
        print("❌ Erreur PostgreSQL:", e)
        db.session.rollback()
        return jsonify({"error": "Erreur base de données"}), 500

@github_bp.route("/github/validate-token", methods=["POST"])
@jwt_required()
def validate_github_token():
    user_id = get_jwt_identity()
    data = request.get_json()
    token = data.get("token")
    selected_repos = data.get("selected_repos", [])

    if not token:
        return jsonify({"error": "Jeton requis"}), 400

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("https://api.github.com/user", headers=headers)
    if response.status_code != 200:
        return jsonify({"error": "Jeton invalide"}), 400

    user_data = response.json()
    github_id = str(user_data["id"])

    repos_response = requests.get("https://api.github.com/user/repos", headers=headers)
    if repos_response.status_code != 200:
        return jsonify({"error": "Échec récupération dépôts"}), 400
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
        return jsonify({"message": "Jeton validé", "repos": repo_data})
    except Exception as e:
        print("❌ Erreur PostgreSQL:", e)
        db.session.rollback()
        return jsonify({"error": "Erreur base de données"}), 500

@github_bp.route("/github/save-repos", methods=["POST"])
@jwt_required()
def save_selected_repos():
    user_id = get_jwt_identity()
    data = request.get_json()
    selected_repos = data.get("selected_repos", [])

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
        return jsonify({"message": "Dépôts enregistrés"})
    except Exception as e:
        print("❌ Erreur PostgreSQL:", e)
        db.session.rollback()
        return jsonify({"error": "Erreur base de données"}), 500

@github_bp.route("/github/repo-configs", methods=["GET"])
@jwt_required()
def get_repo_configs():
    user_id = get_jwt_identity()
    try:
        github_user = GithubUser.query.filter_by(user_id=user_id).first()
        if not github_user:
            return jsonify({"error": "Compte GitHub non lié"}), 404
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
                            # Infer framework
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

        return jsonify(configs)

    except Exception as e:
        print("❌ Erreur:", e)
        db.session.rollback()
        return jsonify({"error": "Erreur serveur"}), 500