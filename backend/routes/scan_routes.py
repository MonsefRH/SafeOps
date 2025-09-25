from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.scan_service import run_scan
from schemas.scan_dto import ScanRequest, ScanResponse, ScanErrorResponse
from pydantic import ValidationError
import logging

scan_bp = Blueprint("scan", __name__)
logger = logging.getLogger(__name__)

@scan_bp.route('/scan', methods=['POST'])
@jwt_required()
def scan_repo():
    try:
        data = ScanRequest(**request.get_json())
        user_id = get_jwt_identity()
        result = run_scan(user_id, data.repo_url)
        return jsonify(ScanResponse(**result).dict()), 200
    except ValidationError as e:
        logger.error(f"Invalid input for scan: {str(e)}")
        return jsonify(ScanErrorResponse(error="Invalid input", details=str(e)).dict()), 400
    except ValueError as e:
        logger.error(f"Scan error: {str(e)}")
        return jsonify(ScanErrorResponse(error=str(e)).dict()), 400
    except RuntimeError as e:
        logger.error(f"Server error during scan: {str(e)}")
        return jsonify(ScanErrorResponse(error=str(e)).dict()), 500