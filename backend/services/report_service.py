# services/report_service.py
import os
import csv
import tempfile
from datetime import datetime
from typing import List, Dict, Any, Tuple
import smtplib
from email.message import EmailMessage

from utils.db import db
from models.scan_history import ScanHistory
from models.user import User
from services.email_template import EMAIL_ADDRESS, EMAIL_PASSWORD

__all__ = ["generate_csv_for_scan", "send_csv_report_email"]

# Colonnes CSV (instant d’exécution uniquement)
CSV_HEADERS = [
    "user_name", "scan_type", "repo", "executed_at",
    "tool", "path", "check_id", "severity", "message",
    "resource", "line_start", "line_end", "status", "suggestion"
]

# ---------- extractors ----------
def _extract_rows_checkov(scan: ScanHistory) -> List[Dict[str, Any]]:
    r = scan.scan_result or {}
    rows = []

    for it in (r.get("failed_checks") or []):
        rows.append({
            "tool": "checkov",
            "path": it.get("file_path") or r.get("path_scanned") or "",
            "check_id": it.get("check_id"),
            "severity": it.get("severity"),
            "message": it.get("check_name"),
            "resource": it.get("resource"),
            "line_start": (it.get("file_line_range") or [None, None])[0],
            "line_end": (it.get("file_line_range") or [None, None])[1],
            "status": "FAILED",
            "suggestion": it.get("suggestion") or "",
        })

    for it in (r.get("passed_checks") or []):
        rows.append({
            "tool": "checkov",
            "path": it.get("file_path") or r.get("path_scanned") or "",
            "check_id": it.get("check_id"),
            "severity": "",
            "message": it.get("check_name"),
            "resource": it.get("resource"),
            "line_start": (it.get("file_line_range") or [None, None])[0],
            "line_end": (it.get("file_line_range") or [None, None])[1],
            "status": "PASSED",
            "suggestion": "",
        })
    return rows

def _extract_rows_semgrep(scan: ScanHistory) -> List[Dict[str, Any]]:
    r = scan.scan_result or {}
    findings = ((r.get("results") or {}).get("failed_checks")) or []
    rows = []
    for it in findings:
        rows.append({
            "tool": "semgrep",
            "path": it.get("file_path") or "",
            "check_id": it.get("check_id"),
            "severity": it.get("severity"),
            "message": it.get("message"),
            "resource": "",
            "line_start": (it.get("file_line_range") or [None, None])[0],
            "line_end": (it.get("file_line_range") or [None, None])[1],
            "status": "FAILED",
            "suggestion": it.get("suggestion") or "",
        })
    return rows

def _extract_rows_t5(scan: ScanHistory) -> List[Dict[str, Any]]:
    r = scan.scan_result or {}
    return [{
        "tool": "t5",
        "path": "Dockerfile",
        "check_id": "T5_CORRECTION",
        "severity": "",
        "message": "T5 correction generated",
        "resource": "",
        "line_start": "",
        "line_end": "",
        "status": (scan.status or "success").upper(),
        "suggestion": (r.get("explanation") or "")[:500],
    }]

def _extract_tool_rows(scan: ScanHistory) -> List[Dict[str, Any]]:
    stype = (scan.scan_type or "").lower()
    if stype == "checkov":
        return _extract_rows_checkov(scan)
    if stype == "semgrep":
        return _extract_rows_semgrep(scan)
    if stype == "t5":
        return _extract_rows_t5(scan)
    return [{
        "tool": stype or "unknown",
        "path": (scan.scan_result or {}).get("path_scanned", ""),
        "check_id": "",
        "severity": "",
        "message": "No parser for this scan_type",
        "resource": "",
        "line_start": "",
        "line_end": "",
        "status": scan.status or "",
        "suggestion": "",
    }]

# ---------- CSV ----------
def generate_csv_for_scan(scan_id: int) -> Tuple[str, str]:
    """
    Génère un CSV pour le scan_id donné.
    Retourne (file_path, filename).
    """
    scan: ScanHistory = db.session.get(ScanHistory, int(scan_id))
    if not scan:
        raise ValueError("scan_id not found")

    user: User = db.session.get(User, int(scan.user_id))
    user_name = user.name if user else "Unknown"

    meta = (scan.scan_result or {}).get("meta", {})
    executed_at = meta.get("executed_at") or (
        scan.created_at.isoformat() if getattr(scan, "created_at", None) else ""
    )

    base_rows = _extract_tool_rows(scan)
    for r in base_rows:
        r.update({
            "user_name": user_name,
            "scan_type": scan.scan_type,
            "repo": scan.repo_url or "local",
            "executed_at": executed_at,
        })

    repo_part = (scan.repo_url or "local").rstrip("/").split("/")[-1]
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    filename = f"safeops_report_{scan.scan_type}_{repo_part}_{scan.id}_{ts}.csv"
    file_path = os.path.join(tempfile.gettempdir(), filename)

    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        for r in base_rows:
            writer.writerow(r)

    return file_path, filename

def send_csv_report_email(
    to_email: str,
    subject: str,
    body_text: str,
    csv_path: str,
    csv_filename: str,
    user_name: str | None = None,
    download_url: str | None = None,
):
    """Send an HTML email with SafeOps blue style and attach the CSV report."""
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email

    greeting_name = (user_name or "there").strip()

    html_body = f"""
    <html>
      <head>
        <style>
          body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background-color: #f5f7fa;
            color: #333;
            margin: 0;
            padding: 0;
          }}
          .container {{
            max-width: 650px;
            margin: 40px auto;
            background: #ffffff;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            overflow: hidden;
          }}
          .header {{
            background: #1565c0;
            color: #fff;
            padding: 20px 30px;
            font-size: 22px;
            font-weight: 600;
          }}
          .content {{
            padding: 30px;
            line-height: 1.6;
          }}
          .footer {{
            background: #f0f3f7;
            color: #666;
            font-size: 13px;
            text-align: center;
            padding: 15px;
          }}
          .btn {{
            display: inline-block;
            background: #1976d2;
            color: white !important;
            padding: 10px 18px;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 500;
          }}
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">SafeOps+ Security Scan Report</div>
          <div class="content">
            <p>Hello <strong>{greeting_name}</strong>,</p>
            <p>{body_text.replace(chr(10), '<br>')}</p>
            <p>You can review the full findings by opening the attached CSV file.</p>
            <p>Thank you for using <strong>SafeOps+</strong>!</p>
          </div>
          <div class="footer">
            &copy; {datetime.utcnow().year} SafeOps+ — Automated Security Platform
          </div>
        </div>
      </body>
    </html>
    """

    msg.set_content("This email contains HTML content. Please enable HTML to view it.")
    msg.add_alternative(html_body, subtype="html")

    with open(csv_path, "rb") as fp:
        data = fp.read()
    msg.add_attachment(data, maintype="text", subtype="csv", filename=csv_filename)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
