from utils.db import db
from models.scan_history import ScanHistory
from sqlalchemy import func
import logging

# Reuse logger from checkov
logger = logging.getLogger(__name__)

def get_user_stats(user_id):
    """Fetch dashboard statistics for a given user."""
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

        return {
            "policies": total_scans,
            "alerts": total_failed,
            "security_score": avg_score
        }
    except Exception as e:
        logger.error(f"Failed to fetch stats for user_id {user_id}: {str(e)}")
        db.session.rollback()
        raise RuntimeError(f"Failed to fetch stats: {str(e)}")