from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_bcrypt import Bcrypt
from services.user_service import register_user, verify_code, login_user, set_password, refresh_token
from schemas.user_dto import (
    RegisterRequest, VerifyCodeRequest, LoginRequest, SetPasswordRequest,
    RegisterResponse, VerifyCodeResponse, LoginResponse, SetPasswordResponse,
    RefreshResponse, ErrorResponse
)
from pydantic import ValidationError
import logging

user_bp = Blueprint("user", __name__)
bcrypt = Bcrypt()
logger = logging.getLogger(__name__)

@user_bp.route("/register", methods=["POST"])
def register():
    try:
        data = RegisterRequest(**request.get_json())
        result = register_user(data.name, data.email, data.password)
        return jsonify(RegisterResponse(**result).dict()), 200
    except ValidationError as e:
        logger.error(f"Invalid input for registration: {str(e)}")
        return jsonify(ErrorResponse(error="Invalid input", details=str(e)).dict()), 400
    except ValueError as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify(ErrorResponse(error=str(e)).dict()), 400
    except RuntimeError as e:
        logger.error(f"Server error during registration: {str(e)}")
        return jsonify(ErrorResponse(error=str(e)).dict()), 500

@user_bp.route("/verify-code", methods=["POST"])
def verify_code_route():
    try:
        data = VerifyCodeRequest(**request.get_json())
        result = verify_code(data.email, data.code)
        return jsonify(VerifyCodeResponse(**result).dict()), 201
    except ValidationError as e:
        logger.error(f"Invalid input for verify-code: {str(e)}")
        return jsonify(ErrorResponse(error="Invalid input", details=str(e)).dict()), 400
    except ValueError as e:
        logger.error(f"Verification error: {str(e)}")
        return jsonify(ErrorResponse(error=str(e)).dict()), 400
    except RuntimeError as e:
        logger.error(f"Server error during verification: {str(e)}")
        return jsonify(ErrorResponse(error=str(e)).dict()), 500

@user_bp.route("/login", methods=["POST"])
def login():
    try:
        data = LoginRequest(**request.get_json())
        result = login_user(request.remote_addr, data.email, data.password)
        return jsonify(LoginResponse(**result).dict()), 200
    except ValidationError as e:
        logger.error(f"Invalid input for login: {str(e)}")
        return jsonify(ErrorResponse(error="Invalid input", details=str(e)).dict()), 400
    except ValueError as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify(ErrorResponse(error=str(e)).dict()), 400 if "blocked" not in str(e).lower() else 429
    except RuntimeError as e:
        logger.error(f"Server error during login: {str(e)}")
        return jsonify(ErrorResponse(error=str(e)).dict()), 500

@user_bp.route("/set-password", methods=["POST"])
@jwt_required()
def set_password_route():
    try:
        data = SetPasswordRequest(**request.get_json())
        user_id = get_jwt_identity()
        result = set_password(user_id, data.password)
        return jsonify(SetPasswordResponse(**result).dict()), 200
    except ValidationError as e:
        logger.error(f"Invalid input for set-password: {str(e)}")
        return jsonify(ErrorResponse(error="Invalid input", details=str(e)).dict()), 400
    except ValueError as e:
        logger.error(f"Set-password error: {str(e)}")
        return jsonify(ErrorResponse(error=str(e)).dict()), 400
    except RuntimeError as e:
        logger.error(f"Server error during set-password: {str(e)}")
        return jsonify(ErrorResponse(error=str(e)).dict()), 500

@user_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    try:
        user_id = get_jwt_identity()
        result = refresh_token(user_id)
        return jsonify(RefreshResponse(**result).dict()), 200
    except RuntimeError as e:
        logger.error(f"Server error during token refresh: {str(e)}")
        return jsonify(ErrorResponse(error=str(e)).dict()), 500