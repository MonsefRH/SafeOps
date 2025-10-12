from utils.db import db
from models.scan_history import ScanHistory
import logging
import json

# Configure logging (keep yours)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s:%(name)s: %(message)s',
    handlers=[logging.FileHandler('risks_app.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Map various tool severities to your 3 buckets
def _normalize_severity(raw: str) -> str:
    if not raw:
        return "INFO"
    s = str(raw).strip().upper()
    # Checkov: CRITICAL/HIGH/MEDIUM/LOW/INFO
    # Semgrep: ERROR/WARNING/INFO
    if s in {"CRITICAL", "HIGH", "ERROR"}:
        return "ERROR"
    if s in {"MEDIUM", "WARNING"}:
        return "WARNING"
    return "INFO"

def _ensure_dict(obj):
    # Accept dict or JSON string
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if isinstance(obj, str):
        try:
            return json.loads(obj)
        except json.JSONDecodeError:
            logger.warning("scan_result is a non-JSON string; ignoring.")
            return {}
    # Unexpected type
    logger.warning(f"scan_result has unexpected type: {type(obj)}")
    return {}

def _extract_checkov_failed_checks(sr: dict):
    """
    Checkov commonly returns either:
    - {"failed_checks": [...]}
    - {"results": {"failed_checks": [...], "parsing_errors": [...], ...}}
    """
    if "failed_checks" in sr and isinstance(sr["failed_checks"], list):
        return sr["failed_checks"]
    results = sr.get("results", {})
    if isinstance(results, dict) and isinstance(results.get("failed_checks"), list):
        return results["failed_checks"]
    return []

def _extract_semgrep_findings(sr: dict):
    """
    Semgrep JSON v1: {"results": [ { "check_id": "...", "path": "...", "start": {...}, "extra": {"severity": "ERROR", "message": "..."} }, ... ] }
    """
    results = sr.get("results")
    if isinstance(results, list):
        return results
    return []

def get_risks(user_id):
    """Fetch and aggregate risks for a user (Checkov + Semgrep)."""
    if not user_id:
        logger.error("Missing user_id for risks")
        raise ValueError("user_id is required")

    try:
        scans = (
            ScanHistory.query
            .filter_by(user_id=user_id)
            .order_by(ScanHistory.created_at.desc())
            .limit(10)
            .all()
        )

        severity_counts = {"ERROR": 0, "WARNING": 0, "INFO": 0}
        detailed_risks = []

        for scan in scans:
            scan_result = _ensure_dict(getattr(scan, "scan_result", None))
            scan_type = getattr(scan, "scan_type", "unknown")

            # 1) Try Checkov shape(s)
            failed_checks = _extract_checkov_failed_checks(scan_result)

            # 2) If no Checkov failed checks, try Semgrep shape
            semgrep_results = []
            if not failed_checks:
                semgrep_results = _extract_semgrep_findings(scan_result)

            # ---- Aggregate Checkov findings ----
            for check in failed_checks:
                sev = _normalize_severity(check.get("severity"))
                severity_counts[sev] += 1

                # Common Checkov fields
                detailed_risks.append({
                    "severity": sev,
                    "check_id": check.get("check_id"),
                    "file_path": check.get("file_path") or check.get("file") or check.get("resource"),
                    "message": check.get("check_name") or check.get("message"),
                    "suggestion": check.get("guideline") or check.get("remediation") or check.get("description"),
                    "scan_type": scan_type or "checkov"
                })

            # ---- Aggregate Semgrep findings ----
            for item in semgrep_results:
                # Semgrep severity in extra.severity
                raw_sev = None
                extra = item.get("extra") if isinstance(item.get("extra"), dict) else {}
                if extra:
                    raw_sev = extra.get("severity")
                sev = _normalize_severity(raw_sev)
                severity_counts[sev] += 1

                # Semgrep fields
                file_path = item.get("path") or item.get("file")
                message = (extra.get("message") if isinstance(extra, dict) else None) or item.get("message")
                check_id = item.get("check_id") or (extra.get("engine_name") if isinstance(extra, dict) else None)

                detailed_risks.append({
                    "severity": sev,
                    "check_id": check_id,
                    "file_path": file_path,
                    "message": message,
                    "suggestion": extra.get("metadata", {}).get("fix") if isinstance(extra.get("metadata"), dict) else None,
                    "scan_type": scan_type or "semgrep"
                })

        # Format risks for dashboard (keep your scaling)
        risks = [
            {"name": "Critical (ERROR)", "level": severity_counts.get("ERROR", 0) * 10},
            {"name": "High (WARNING)",  "level": severity_counts.get("WARNING", 0) * 5},
            {"name": "Low (INFO)",      "level": severity_counts.get("INFO", 0) * 2},
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
