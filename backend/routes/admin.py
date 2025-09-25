from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.admin_service import get_admin_stats
from schemas.admin_dto import AdminStatsResponse
from pydantic import ValidationError

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/api/admin-stats", methods=["GET"])
@jwt_required()
def get_admin_stats_route():
    try:
        user_id = get_jwt_identity()
        stats = get_admin_stats(user_id)
        return jsonify(AdminStatsResponse(**stats).dict()), 200
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 403
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500