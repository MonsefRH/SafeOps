from flask import Blueprint, request, jsonify
from routes.checkov import logger
from utils.db import get_db_connection

history_bp = Blueprint('history', __name__)


@history_bp.route("/history", methods=["GET"])
def get_scan_history():
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    scan_type = request.args.get("scan_type")  # Get scan_type from query params

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Base query
        query = """
            SELECT id, repo_id, scan_result, repo_url, status, score, compliant, created_at, input_type, scan_type
            FROM scan_history
            WHERE user_id = %s
        """
        params = [user_id]

        # Add scan_type filter if provided
        if scan_type:
            query += " AND scan_type = %s"
            params.append(scan_type)

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        history = []

        for row in rows:
            input_type = row[8]
            item_name = None
            if input_type and input_type != "":
                scan_id = row[0]
                cursor.execute(
                    """
                    SELECT id, scan_id, file_path, content, input_type, created_at
                    FROM file_contents
                    WHERE scan_id = %s
                    """,
                    (scan_id,)
                )
                file_row = cursor.fetchone()
                if file_row:
                    item_name = f"{file_row[2]} {file_row[0]}"  # file_path + id
                    logger.debug(f"Item name for scan_id {scan_id}: {item_name}")

            element = {
                "id": row[0],
                "repo_id": row[1],
                "scan_result": row[2],
                "repo_url": row[3],
                "item_name": item_name,
                "status": row[4],
                "score": row[5],
                "compliant": row[6],
                "created_at": row[7].isoformat(),
                "input_type": row[8],
                "scan_type": row[9]
            }
            history.append(element)

        return jsonify(history)
    except Exception as e:
        logger.error(f"Failed to fetch scan history for user_id {user_id}: {str(e)}")
        return jsonify({"error": "Failed to fetch scan history"}), 500
    finally:
        cursor.close()
        conn.close()