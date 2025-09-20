from flask import Blueprint, jsonify, request
from routes.checkov import logger
from utils.db import db
from models.scan_history import ScanHistory
from sqlalchemy import func

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/stats", methods=["GET"])
def get_stats():
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    try:
        # Total scans
        total_scans = ScanHistory.query.filter_by(user_id=user_id).count()

        # Total failed checks
        total_failed = (
            db.session.query(
                func.sum(func.cast(ScanHistory.scan_result["results"]["summary"]["failed"], db.Integer))
            )
            .filter_by(user_id=user_id)
            .scalar() or 0
        )

        # Total passed checks
        total_passed = (
            db.session.query(
                func.sum(func.cast(ScanHistory.scan_result["results"]["summary"]["passed"], db.Integer))
            )
            .filter_by(user_id=user_id)
            .scalar() or 0
        )

        # Average security score
        avg_score = (
            db.session.query(
                func.avg(func.cast(ScanHistory.scan_result["results"]["score"], db.Integer))
            )
            .filter_by(user_id=user_id)
            .scalar() or 0
        )
        avg_score = round(float(avg_score))

        return jsonify({
            "policies": total_scans,  # Number of scans as "policies"
            "alerts": total_failed,   # Total failed checks as "alerts"
            "securityScore": avg_score  # Average score as "securityScore"
        })
    except Exception as e:
        logger.error(f"Failed to fetch stats for user_id {user_id}: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Failed to fetch stats"}), 500