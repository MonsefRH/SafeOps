from flask import Blueprint, request, jsonify, redirect
from services.google_service import google_login, google_callback
from schemas.google_dto import GoogleAuthResponse, GoogleCallbackResponse, GoogleErrorResponse
import logging

google_bp = Blueprint("google", __name__)
logger = logging.getLogger(__name__)

@google_bp.route("/auth/google", methods=["GET"])
def google_login_route():
    try:
        auth_url = google_login()
        return jsonify(GoogleAuthResponse(authorization_url=auth_url).dict()), 200
    except ValueError as e:
        logger.error(f"Google login error: {str(e)}")
        return jsonify(GoogleErrorResponse(error=str(e)).dict()), 400

@google_bp.route("/auth/google/callback", methods=["GET"])
def google_callback_route():
    try:
        code = request.args.get("code")
        frontend_url = google_callback(code)
        return redirect(GoogleCallbackResponse(redirect_url=frontend_url).redirect_url)
    except ValueError as e:
        logger.error(f"Google callback error: {str(e)}")
        return jsonify(GoogleErrorResponse(error=str(e)).dict()), 400
    except RuntimeError as e:
        logger.error(f"Database error in Google callback: {str(e)}")
        return jsonify(GoogleErrorResponse(error=str(e)).dict()), 500