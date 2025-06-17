from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from routes.checkov import logger
from utils.db import get_db_connection

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/stats", methods=["GET"])
def get_stats():
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Total scans
        cursor.execute("SELECT COUNT(*) FROM scan_history WHERE user_id = %s", (user_id,))
        total_scans = cursor.fetchone()[0]

        # Total failed checks
        cursor.execute(
            """
            SELECT SUM((scan_result->'results'->'summary'->>'failed')::int)
            FROM scan_history
            WHERE user_id = %s
            """,
            (user_id,)
        )
        total_failed = cursor.fetchone()[0] or 0

        # Total passed checks
        cursor.execute(
            """
            SELECT SUM((scan_result->'results'->'summary'->>'passed')::int)
            FROM scan_history
            WHERE user_id = %s
            """,
            (user_id,)
        )
        total_passed = cursor.fetchone()[0] or 0

        # Average security score
        cursor.execute(
            """
            SELECT AVG((scan_result->'results'->>'score')::int)
            FROM scan_history
            WHERE user_id = %s
            """,
            (user_id,)
        )
        avg_score = cursor.fetchone()[0] or 0
        avg_score = round(float(avg_score))

        return jsonify({
            "policies": total_scans,  # Number of scans as "policies"
            "alerts": total_failed,   # Total failed checks as "alerts"
            "securityScore": avg_score  # Average score as "securityScore"
        })
    except Exception as e:
        logger.error(f"Failed to fetch stats for user_id {user_id}: {str(e)}")
        return jsonify({"error": "Failed to fetch stats"}), 500
    finally:
        cursor.close()
        conn.close()
