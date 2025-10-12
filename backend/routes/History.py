from flask import Blueprint, request, jsonify
from services.history_service import get_scan_history
from schemas.history_dto import ScanHistoryResponse, HistoryErrorResponse
import logging

from flasgger import swag_from
history_bp = Blueprint("history", __name__)
logger = logging.getLogger(__name__)

@history_bp.route("/history", methods=["GET"])
@swag_from("../specs/history_specs.yml")
def get_scan_history_route():
    user_id = request.headers.get("X-User-ID")
    scan_type = request.args.get("scan_type")

    try:
        history = get_scan_history(user_id, scan_type)
        return jsonify([ScanHistoryResponse(**item).dict() for item in history]), 200
    except ValueError as e:
        logger.error(f"Invalid input for scan history: {str(e)}")
        return jsonify(HistoryErrorResponse(error=str(e)).dict()), 400
    except RuntimeError as e:
        logger.error(f"Error fetching scan history: {str(e)}")
        return jsonify(HistoryErrorResponse(error=str(e)).dict()), 500