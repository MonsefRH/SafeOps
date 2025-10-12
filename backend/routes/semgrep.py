from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.semgrep_service import validate_semgrep
from schemas.semgrep_dto import SemgrepResponse, SemgrepErrorResponse
import logging

from flasgger import swag_from

semgrep_bp = Blueprint("semgrep", __name__)
logger = logging.getLogger(__name__)

@semgrep_bp.route("/semgrep", methods=["POST"])
@jwt_required()
@swag_from("../specs/semgrep_specs.yml")
def validate_semgrep_route():
    try:
        user_id = get_jwt_identity()
        input_type = request.form.get("input_type")
        file = request.files.get("file")
        repo_url = request.form.get("repo_url")
        content = request.form.get("content")
        extension = request.form.get("extension", "py")

        result = validate_semgrep(user_id, input_type, file, repo_url, content, extension)
        return jsonify(SemgrepResponse(**result).dict()), 200
    except ValueError as e:
        logger.error(f"Invalid input for Semgrep scan: {str(e)}")
        return jsonify(SemgrepErrorResponse(error=str(e)).dict()), 400
    except RuntimeError as e:
        logger.error(f"Server error during Semgrep scan: {str(e)}")
        return jsonify(SemgrepErrorResponse(error=str(e)).dict()), 500