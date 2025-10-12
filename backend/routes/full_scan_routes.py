from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.full_scan_service import run_full_scan
from schemas.full_scan_dto import FullScanResponse, FullScanRequest, FullScanErrorResponse
from pydantic import ValidationError
import logging

from flasgger import swag_from
full_scan_bp = Blueprint("full_scan", __name__)
logger = logging.getLogger(__name__)

@full_scan_bp.route("/full-scan", methods=["POST"])
@jwt_required()
@swag_from("../specs/full_scan_specs.yml")
def full_scan():
    try:
        data = FullScanRequest(**request.get_json())
        user_id = get_jwt_identity()
        jwt_token = request.headers.get("Authorization")
        results = run_full_scan(user_id, data.repo_url, jwt_token)
        return jsonify(FullScanResponse(**results).dict()), 200
    except ValidationError as e:
        return jsonify(FullScanErrorResponse(error="Invalid input", details=str(e)).dict()), 400
    except RuntimeError as e:
        return jsonify(FullScanErrorResponse(error=str(e)).dict()), 500
    except Exception as e:
        logger.exception("Unexpected error in full scan")
        return jsonify(FullScanErrorResponse(error=f"Internal server error: {str(e)}").dict()), 500