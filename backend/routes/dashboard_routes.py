from flask import Blueprint, jsonify, request
from services.dashboard_service import get_user_stats
from schemas.dashboard_dto import DashboardStatsResponse, DashboardErrorResponse

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/stats", methods=["GET"])
def get_stats():
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        return jsonify(DashboardErrorResponse(error="user_id is required").dict()), 400

    try:
        stats = get_user_stats(user_id)
        return jsonify(DashboardStatsResponse(**stats).dict()), 200
    except RuntimeError as e:
        return jsonify(DashboardErrorResponse(error=str(e)).dict()), 500