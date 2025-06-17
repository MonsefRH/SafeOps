from flask import Blueprint, request, jsonify, redirect
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from utils.db import get_db_connection
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

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Erreur connexion DB"}), 500

        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, name, email, password FROM users_test WHERE email = %s",
                    (email,)
                )
                user = cur.fetchone()

                if user:
                    user_id = user[0]
                    needs_password = user[3] is None
                else:
                    cur.execute(
                        "INSERT INTO users_test (name, email, created_at) VALUES (%s, %s, CURRENT_TIMESTAMP) RETURNING id",
                        (name, email)
                    )
                    user_id = cur.fetchone()[0]
                    needs_password = True

                cur.execute(
                    "SELECT user_id FROM github_users WHERE github_id = %s",
                    (github_id,)
                )
                github_user = cur.fetchone()

                if not github_user:
                    cur.execute(
                        "INSERT INTO github_users (user_id, github_id, access_token, created_at) "
                        "VALUES (%s, %s, %s, CURRENT_TIMESTAMP)",
                        (user_id, github_id, access_token)
                    )

                conn.commit()

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
            conn.rollback()
            return jsonify({"error": "Erreur base de données"}), 500
        finally:
            conn.close()

    except Exception as e:
        print("❌ Erreur GitHub OAuth:", e)
        return jsonify({"error": "Erreur d'authentification"}), 500

@github_bp.route("/github/repos", methods=["GET"])
@jwt_required()
def get_github_repos():
    user_id = get_jwt_identity()
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Erreur connexion DB"}), 500

    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT access_token FROM github_users WHERE user_id = %s",
                (user_id,)
            )
            result = cur.fetchone()
            if not result:
                return jsonify({"error": "Compte GitHub non lié"}), 404
            access_token = result[0]

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
        with conn.cursor() as cur:
            cur.execute(
                "SELECT full_name FROM selected_repos WHERE user_id = %s",
                (user_id,)
            )
            selected = [row[0] for row in cur.fetchall()]
            for repo in repo_data:
                repo["is_selected"] = repo["full_name"] in selected
        return jsonify(repo_data)

    except Exception as e:
        print("❌ Erreur PostgreSQL:", e)
        return jsonify({"error": "Erreur base de données"}), 500
    finally:
        conn.close()

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

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Erreur connexion DB"}), 500

    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id FROM github_users WHERE user_id = %s",
                (user_id,)
            )
            exists = cur.fetchone()
            if exists:
                cur.execute(
                    "UPDATE github_users SET access_token = %s, github_id = %s WHERE user_id = %s",
                    (token, github_id, user_id)
                )
            else:
                cur.execute(
                    "INSERT INTO github_users (user_id, github_id, access_token, created_at) "
                    "VALUES (%s, %s, %s, CURRENT_TIMESTAMP)",
                    (user_id, github_id, token)
                )
            conn.commit()
        return jsonify({"message": "Jeton validé", "repos": repo_data})
    except Exception as e:
        print("❌ Erreur PostgreSQL:", e)
        conn.rollback()
        return jsonify({"error": "Erreur base de données"}), 500
    finally:
        conn.close()

@github_bp.route("/github/save-repos", methods=["POST"])
@jwt_required()
def save_selected_repos():
    user_id = get_jwt_identity()
    data = request.get_json()
    selected_repos = data.get("selected_repos", [])

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Erreur connexion DB"}), 500

    try:
        with conn.cursor() as cur:
            # Clear existing selections
            cur.execute(
                "DELETE FROM selected_repos WHERE user_id = %s",
                (user_id,)
            )

            # Insert new selections
            for repo in selected_repos:
                cur.execute(
                    "INSERT INTO selected_repos (user_id, full_name, name, html_url, created_at) "
                    "VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP) ON CONFLICT (full_name) DO NOTHING",
                    (user_id, repo["full_name"], repo["name"], repo["html_url"])
                )

            conn.commit()
        return jsonify({"message": "Dépôts enregistrés"})
    except Exception as e:
        print("❌ Erreur PostgreSQL:", e)
        conn.rollback()
        return jsonify({"error": "Erreur base de données"}), 500
    finally:
        conn.close()

# github.py (Flask Blueprint)
@github_bp.route("/github/repo-configs", methods=["GET"])
@jwt_required()
def get_repo_configs():
    user_id = get_jwt_identity()
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Erreur connexion DB"}), 500

    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT access_token FROM github_users WHERE user_id = %s",
                (user_id,)
            )
            result = cur.fetchone()
            if not result:
                return jsonify({"error": "Compte GitHub non lié"}), 404
            access_token = result[0]

            cur.execute(
                "SELECT id, full_name, html_url FROM selected_repos WHERE user_id = %s",
                (user_id,)
            )
            repos = [{"id": row[0], "full_name": row[1], "html_url": row[2]} for row in cur.fetchall()]

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

            with conn.cursor() as cur:
                for config in repo_configs:
                    content_bytes = config["content"].encode("utf-8")
                    cur.execute(
                        "INSERT INTO repo_configs (repo_id, file_path, file_name, content, sha, framework, created_at) "
                        "VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP) "
                        "ON CONFLICT (file_path, repo_id) DO UPDATE SET content = EXCLUDED.content, sha = EXCLUDED.sha, framework = EXCLUDED.framework",
                        (config["repo_id"], config["file_path"], config["file_name"], content_bytes, config["sha"], config["framework"])
                    )
                conn.commit()

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT rc.id, rc.file_path, rc.file_name, rc.content, rc.sha, sr.full_name, sr.html_url, rc.framework
                FROM repo_configs rc
                JOIN selected_repos sr ON rc.repo_id = sr.id
                WHERE sr.user_id = %s
                """,
                (user_id,)
            )
            configs = [
                {
                    "id": row[0],
                    "file_path": row[1],
                    "file_name": row[2],
                    "content": bytes(row[3]).decode("utf-8", errors="ignore"),  # Convert memoryview to bytes first
                    "sha": row[4],
                    "repo_full_name": row[5],
                    "repo_html_url": row[6],
                    "framework": row[7]
                }
                for row in cur.fetchall()
            ]

        return jsonify(configs)

    except Exception as e:
        print("❌ Erreur:", e)
        return jsonify({"error": "Erreur serveur"}), 500
    finally:
        conn.close()