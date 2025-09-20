from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.db import db
from models.user import User
from models.scan_history import ScanHistory
from sqlalchemy import func

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/api/admin-stats", methods=["GET"])
@jwt_required()
def get_admin_stats():
    user_id = get_jwt_identity()

    try:
        # Verify user is admin
        user = User.query.filter_by(id=user_id).first()
        if not user or user.role != "admin":
            return jsonify({"error": "Access denied: Admin role required"}), 403

        # Get total users (with role 'user')
        total_users = User.query.filter_by(role="user").count()

        # Get total scans
        total_scans = ScanHistory.query.count()

        # Get user data with scan counts
        users = (
            db.session.query(
                User.id,
                User.name,
                User.email,
                User.role,
                User.created_at,
                func.count(ScanHistory.id).label("scan_count")
            )
            .outerjoin(ScanHistory, User.id == ScanHistory.user_id)
            .filter(User.role == "user")
            .group_by(User.id, User.name, User.email, User.role, User.created_at)
            .order_by(User.created_at.desc())
            .all()
        )

        # Format users data for response
        users_data = [
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "created_at": user.created_at.isoformat(),
                "scan_count": user.scan_count
            }
            for user in users
        ]

        return jsonify({
            "totalUsers": total_users,
            "totalScans": total_scans,
            "users": users_data
        })

    except Exception as e:
        print(f"❌ Error fetching admin stats: {e}")
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500