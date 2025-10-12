from flask import Blueprint, request, jsonify
from services.checkov_service import run_checkov_scan
from schemas.checkov_dto import CheckovResponse, CheckovContentRequest, CheckovRepoRequest, CheckovErrorResponse
from pydantic import ValidationError
import os
import logging

from flasgger import swag_from
checkov_bp = Blueprint("checkov", __name__)

# Configure upload folder
UPLOAD_FOLDER = "Uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configure logging
logger = logging.getLogger(__name__)

@checkov_bp.route("/checkov", methods=["POST"])
@swag_from("../specs/checkov_specs.yml")
def validate():
    try:
        user_id = request.headers.get("X-User-ID") or (request.json and request.json.get("user_id"))
        if not user_id:
            return jsonify(CheckovErrorResponse(error="user_id is required").dict()), 400

        input_type = request.form.get("input_type")

        # Handle JSON input (content or repo_url)
        if not input_type and request.is_json:
            data = request.get_json()
            if "content" in data:
                input_data = CheckovContentRequest(**data)
                result = run_checkov_scan(user_id, input_type="content", content=input_data.content)
                return jsonify(CheckovResponse(**result).dict()), 200
            if "repo_url" in data:
                input_type = "repo"
                input_data = CheckovRepoRequest(**data)
                request.form = data

        if input_type == "file" and "file" in request.files:
            file = request.files["file"]
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            try:
                file.save(file_path)
                result = run_checkov_scan(user_id, input_type="file", file_path=file_path)
                return jsonify(CheckovResponse(**result).dict()), 200
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)

        elif input_type == "zip" and "file" in request.files:
            file = request.files["file"]
            zip_path = os.path.join(UPLOAD_FOLDER, file.filename)
            try:
                file.save(zip_path)
                result = run_checkov_scan(user_id, input_type="zip", zip_path=zip_path)
                return jsonify(CheckovResponse(**result).dict()), 200
            finally:
                if os.path.exists(zip_path):
                    os.remove(zip_path)

        elif input_type == "repo":
            repo_url = request.form.get("repo_url") or (request.json and request.json.get("repo_url"))
            try:
                CheckovRepoRequest(repo_url=repo_url)
                result = run_checkov_scan(user_id, input_type="repo", repo_url=repo_url)
                return jsonify(CheckovResponse(**result).dict()), 200
            except ValidationError as e:
                return jsonify(CheckovErrorResponse(error="Invalid repo_url", details=str(e)).dict()), 400

        return jsonify(CheckovErrorResponse(error="Type d'entrée invalide. Utilisez 'file', 'zip', 'repo' ou 'content'").dict()), 400

    except ValidationError as e:
        return jsonify(CheckovErrorResponse(error="Invalid input", details=str(e)).dict()), 400
    except ValueError as e:
        return jsonify(CheckovErrorResponse(error=str(e)).dict()), 400
    except Exception as e:
        logger.error(f"Unexpected error in Checkov route: {str(e)}")
        return jsonify(CheckovErrorResponse(error="Internal server error", details=str(e)).dict()), 500