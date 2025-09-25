from utils.db import db
from models.scan_history import ScanHistory
from models.file_content import FileContent
import logging

# Reuse logger from checkov
logger = logging.getLogger(__name__)

def get_scan_history(user_id, scan_type=None):
    """Fetch scan history for a user, optionally filtered by scan type."""
    if not user_id:
        logger.error("Missing user_id for scan history")
        raise ValueError("user_id is required")

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

        logger.info(f"Fetched {len(history)} scan history records for user_id {user_id}")
        return history

    except Exception as e:
        logger.error(f"Failed to fetch scan history for user_id {user_id}: {str(e)}")
        db.session.rollback()
        raise RuntimeError("Failed to fetch scan history")