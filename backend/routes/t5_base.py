from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.t5_service import correct_dockerfile
from schemas.t5_dto import T5Request, T5Response, T5ErrorResponse
from pydantic import ValidationError
import logging

t5_base_bp = Blueprint("t5", __name__)
logger = logging.getLogger(__name__)

@t5_base_bp.route("/t5", methods=["POST"])
@jwt_required()
def correct_dockerfile_route():
    try:
        data = T5Request(**request.get_json())
        user_id = get_jwt_identity()
        result = correct_dockerfile(user_id, data.dockerfile)
        return jsonify(T5Response(**result).dict()), 200
    except ValidationError as e:
        logger.error(f"Invalid input for T5 correction: {str(e)}")
        return jsonify(T5ErrorResponse(error="Invalid input", details=str(e)).dict()), 400
    except ValueError as e:
        logger.error(f"T5 correction error: {str(e)}")
        return jsonify(T5ErrorResponse(error=str(e)).dict()), 400
    except RuntimeError as e:
        logger.error(f"Server error during T5 correction: {str(e)}")
        return jsonify(T5ErrorResponse(error=str(e)).dict()), 500