from utils.db import db
from models.scan_history import ScanHistory
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s:%(name)s: %(message)s',
    handlers=[logging.FileHandler('risks_app.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def get_risks(user_id):
    """Fetch and aggregate risks for a user."""
    if not user_id:
        logger.error("Missing user_id for risks")
        raise ValueError("user_id is required")

    try:
        # Fetch scan history
        scans = (
            ScanHistory.query
            .filter_by(user_id=user_id)
            .order_by(ScanHistory.created_at.desc())
            .limit(10)
            .all()
        )

        # Aggregate risks by severity
        severity_counts = {"ERROR": 0, "WARNING": 0, "INFO": 0}
        detailed_risks = []

        for scan in scans:
            scan_result = scan.scan_result
            scan_type = scan.scan_type
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

        logger.info(f"Fetched risks for user_id {user_id}: {len(detailed_risks)} detailed risks")
        return {
            "risks": risks,
            "details": detailed_risks
        }

    except Exception as e:
        logger.error(f"Failed to fetch risks for user_id {user_id}: {str(e)}")
        db.session.rollback()
        raise RuntimeError("Failed to fetch risks")