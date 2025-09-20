from flask import Blueprint, request, jsonify
from routes.checkov import logger
from utils.db import db
from models.scan_history import ScanHistory
from models.file_content import FileContent

history_bp = Blueprint('history', __name__)

@history_bp.route("/history", methods=["GET"])
def get_scan_history():
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    scan_type = request.args.get("scan_type")

    try:
        # Base query
        query = ScanHistory.query.filter_by(user_id=user_id)
        
        # Add scan_type filter if provided
        if scan_type:
            query = query.filter_by(scan_type=scan_type)
        
        # Order by created_at DESC
        query = query.order_by(ScanHistory.created_at.desc())
        
        history = []
        for scan in query.all():
            item_name = None
            if scan.input_type:
                file_content = FileContent.query.filter_by(scan_id=scan.id).first()
                if file_content:
                    item_name = f"{file_content.file_path} {file_content.id}"
                    logger.debug(f"Item name for scan_id {scan.id}: {item_name}")

            element = {
                "id": scan.id,
                "repo_id": scan.repo_id,
                "scan_result": scan.scan_result,
                "repo_url": scan.repo_url,
                "item_name": item_name,
                "status": scan.status,
                "score": scan.score,
                "compliant": scan.compliant,
                "created_at": scan.created_at.isoformat(),
                "input_type": scan.input_type,
                "scan_type": scan.scan_type
            }
            history.append(element)

        return jsonify(history)
    except Exception as e:
        logger.error(f"Failed to fetch scan history for user_id {user_id}: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Failed to fetch scan history"}), 500