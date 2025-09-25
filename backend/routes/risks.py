from flask import Blueprint, request, jsonify
from services.risks_service import get_risks
from schemas.risks_dto import RisksResponse, RisksErrorResponse
import logging

risks_bp = Blueprint("risks", __name__)
logger = logging.getLogger(__name__)

@risks_bp.route("/risks", methods=["GET"])
def get_risks_route():
    user_id = request.headers.get("X-User-ID")
    try:
        risks_data = get_risks(user_id)
        return jsonify(RisksResponse(**risks_data).dict()), 200
    except ValueError as e:
        logger.error(f"Invalid input for risks: {str(e)}")
        return jsonify(RisksErrorResponse(error=str(e)).dict()), 400
    except RuntimeError as e:
        logger.error(f"Error fetching risks: {str(e)}")
        return jsonify(RisksErrorResponse(error=str(e)).dict()), 500