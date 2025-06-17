from flask import Blueprint, request, jsonify
from utils.db import get_db_connection
import logging

risks_bp = Blueprint('risks', __name__)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s:%(name)s: %(message)s',
    handlers=[logging.FileHandler('risks_app.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


@risks_bp.route("/risks", methods=["GET"])
def get_risks():
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch scan history
        query = """
            SELECT scan_result, scan_type
            FROM scan_history
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 10
        """
        cursor.execute(query, (user_id,))
        rows = cursor.fetchall()

        # Aggregate risks by severity
        severity_counts = {"ERROR": 0, "WARNING": 0, "INFO": 0}
        detailed_risks = []

        for row in rows:
            scan_result = row[0]
            scan_type = row[1]
            failed_checks = scan_result.get("results", {}).get("failed_checks", [])

            for check in failed_checks:
                severity = check.get("severity", "INFO")
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
                detailed_risks.append({
                    "severity": severity,
                    "check_id": check.get("check_id"),
                    "file_path": check.get("file_path"),
                    "message": check.get("message"),
                    "suggestion": check.get("suggestion"),
                    "scan_type": scan_type
                })

        # Format risks for dashboard
        risks = [
            {"name": "Critical (ERROR)", "level": severity_counts.get("ERROR", 0) * 10},  # Scale for display
            {"name": "High (WARNING)", "level": severity_counts.get("WARNING", 0) * 5},
            {"name": "Low (INFO)", "level": severity_counts.get("INFO", 0) * 2}
        ]

        return jsonify({
            "risks": risks,
            "details": detailed_risks
        })
    except Exception as e:
        logger.error(f"Failed to fetch risks for user_id {user_id}: {str(e)}")
        return jsonify({"error": "Failed to fetch risks"}), 500
    finally:
        cursor.close()
        conn.close()