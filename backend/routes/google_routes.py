from flask import Blueprint, request, jsonify, redirect
from flask_jwt_extended import create_access_token, create_refresh_token
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport.requests import Request
from utils.db import get_db_connection
import os
from dotenv import load_dotenv

load_dotenv()

google_bp = Blueprint("google", __name__)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = "http://localhost:5000/auth/google/callback"
SCOPES = ["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"]

@google_bp.route("/auth/google", methods=["GET"])
def google_login():
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uris": [GOOGLE_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES
    )
    flow.redirect_uri = GOOGLE_REDIRECT_URI
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )
    return jsonify({"authorization_url": authorization_url})

@google_bp.route("/auth/google/callback", methods=["GET"])
def google_callback():
    try:
        code = request.args.get("code")
        if not code:
            return jsonify({"error": "Code d'autorisation manquant"}), 400

        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "redirect_uris": [GOOGLE_REDIRECT_URI],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=SCOPES
        )
        flow.redirect_uri = GOOGLE_REDIRECT_URI
        flow.fetch_token(code=code)

        credentials = flow.credentials
        id_info = id_token.verify_oauth2_token(
            credentials.id_token, Request(), GOOGLE_CLIENT_ID
        )

        email = id_info.get("email")
        name = id_info.get("name", "Utilisateur Google")

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Erreur de connexion à la base de données"}), 500

        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, name, email, password FROM users_test WHERE email = %s", (email,))
                user = cur.fetchone()

                if user:
                    user_id = user[0]
                    needs_password = user[3] is None
                else:
                    cur.execute(
                        "INSERT INTO users_test (name, email) VALUES (%s, %s) RETURNING id",
                        (name, email)
                    )
                    user_id = cur.fetchone()[0]
                    conn.commit()
                    needs_password = True

                access_token = create_access_token(identity=str(user_id))
                refresh_token = create_refresh_token(identity=str(user_id))

                frontend_url = (
                    f"http://localhost:3000/auth/google/callback"
                    f"?access_token={access_token}"
                    f"&refresh_token={refresh_token}"
                    f"&user_id={user_id}"
                    f"&name={name}"
                    f"&email={email}"
                    f"&needs_password={str(needs_password).lower()}"
                )
                return redirect(frontend_url)

        except Exception as e:
            print("❌ Erreur lors de l'authentification Google :", e)
            return jsonify({"error": "Erreur lors de l'authentification"}), 500
        finally:
            conn.close()

    except Exception as e:
        print("❌ Erreur Google OAuth :", e)
        return jsonify({"error": "Erreur lors de l'authentification Google"}), 500