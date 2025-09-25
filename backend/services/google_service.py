from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport.requests import Request
from utils.db import db
from models.user import User
from flask_jwt_extended import create_access_token, create_refresh_token
import os
from dotenv import load_dotenv
import logging

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = "http://localhost:5000/auth/google/callback"
SCOPES = ["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"]

def google_login():
    """Generate Google OAuth authorization URL."""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        logger.error("Google client credentials not configured")
        raise ValueError("Google client credentials not configured")

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
    logger.debug(f"Generated Google OAuth URL: {authorization_url}")
    return authorization_url

def google_callback(code):
    """Handle Google OAuth callback and create/update user."""
    if not code:
        logger.error("Missing authorization code")
        raise ValueError("Code d'autorisation manquant")

    try:
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
        if not email:
            logger.error("No email found in Google ID token")
            raise ValueError("Email non trouvé")
        
        name = id_info.get("name", "Utilisateur Google")

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

            db.session.commit()
            logger.info(f"User {email} (ID: {user_id}) authenticated via Google")

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
            return frontend_url

        except Exception as e:
            logger.error(f"Database error during Google callback: {str(e)}")
            db.session.rollback()
            raise RuntimeError("Erreur lors de l'authentification")

    except Exception as e:
        logger.error(f"Google OAuth error: {str(e)}")
        raise ValueError("Erreur lors de l'authentification Google")