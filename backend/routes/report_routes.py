from flask import Blueprint, send_file, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.db import db
from models.scan_history import ScanHistory
from models.user import User
from services.report_service import generate_csv_for_scan, send_csv_report_email

from flasgger import swag_from

report_bp = Blueprint("reports", __name__)

@report_bp.route("/reports/<int:scan_id>/csv", methods=["GET"])
@jwt_required()
@swag_from("../specs/reports_specs.yml")
def download_report_csv(scan_id: int):
    user_id = int(get_jwt_identity())
    scan: ScanHistory = db.session.get(ScanHistory, scan_id)
    if not scan:
        return jsonify({"error": "scan not found"}), 404

    user = db.session.get(User, user_id)
    if (scan.user_id != user_id) and (user.role != "admin"):
        return jsonify({"error": "forbidden"}), 403

    try:
        csv_path, csv_filename = generate_csv_for_scan(scan_id)

        if request.args.get("email", "false").lower() == "true":
            subject = f"SafeOps — Rapport CSV ({scan.scan_type})"
            executed_at = ((scan.scan_result or {}).get("meta", {}) or {}).get("executed_at", scan.created_at.isoformat() if getattr(scan, "created_at", None) else "")
            body = f"Bonjour {user.name},\n\nVeuillez trouver ci-joint le rapport CSV de votre scan.\nExécuté le : {executed_at}\n"
            send_csv_report_email(user.email, subject, body, csv_path, csv_filename)

        return send_file(csv_path, mimetype="text/csv", as_attachment=True, download_name=csv_filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 500