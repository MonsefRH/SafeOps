from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.db import get_db_connection

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/api/admin-stats", methods=["GET"])
@jwt_required()
def get_admin_stats():
    user_id = get_jwt_identity()
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        with conn.cursor() as cur:
            # Verify user is admin
            cur.execute("SELECT role FROM users WHERE id = %s", (user_id,))
            user = cur.fetchone()
            if not user or user[0] != "admin":
                return jsonify({"error": "Access denied: Admin role required"}), 403

            # Get total users
            cur.execute("SELECT COUNT(*) FROM users where role = 'user'")
            total_users = cur.fetchone()[0]

            # Get total scans
            cur.execute("SELECT COUNT(*) FROM scan_history")
            total_scans = cur.fetchone()[0]

            # Get user data with scan counts
            cur.execute("""
                SELECT 
                    u.id, 
                    u.name, 
                    u.email, 
                    u.role, 
                    u.created_at, 
                    COUNT(sh.id) as scan_count
                FROM users u
                LEFT JOIN scan_history sh ON u.id = sh.user_id
                Where role = 'user'
                GROUP BY u.id, u.name, u.email, u.role, u.created_at
                ORDER BY u.created_at DESC
            """)
            users = [
                {
                    "id": row[0],
                    "name": row[1],
                    "email": row[2],
                    "role": row[3],
                    "created_at": row[4].isoformat(),
                    "scan_count": row[5]
                }
                for row in cur.fetchall()
            ]

            return jsonify({
                "totalUsers": total_users,
                "totalScans": total_scans,
                "users": users
            })

    except Exception as e:
        print(f"❌ Error fetching admin stats: {e}")
        return jsonify({"error": "Internal server error"}), 500

    finally:
        conn.close()