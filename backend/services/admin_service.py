from utils.db import db
from models.user import User
from models.scan_history import ScanHistory
from sqlalchemy import func

def get_admin_stats(user_id):
    """Fetch admin statistics if the user is an admin."""
    # Verify user is admin
    user = User.query.filter_by(id=user_id).first()
    if not user or user.role != "admin":
        raise ValueError("Access denied: Admin role required")

    try:
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

        # Format users data
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

        return {
            "total_users": total_users,
            "total_scans": total_scans,
            "users": users_data
        }
    except Exception as e:
        db.session.rollback()
        raise RuntimeError(f"Error fetching admin stats: {str(e)}")