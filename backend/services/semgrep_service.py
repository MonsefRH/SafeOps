from pathlib import Path
import os
import tempfile
import zipfile
import subprocess
import shutil
import json
import logging
import time

import google.generativeai as genai
from git import Repo

from utils.db import db
from models.scan_history import ScanHistory
from models.user import User

# Email + CSV
from services.report_service import generate_csv_for_scan, send_csv_report_email


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s:%(name)s: %(message)s',
    handlers=[logging.FileHandler('semgrep_app.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY environment variable not set.")
    raise ValueError("GEMINI_API_KEY environment variable not set.")
genai.configure(api_key=GEMINI_API_KEY)


def clean_path(full_path: str) -> str:
    """Remove temp-dir prefixes from file paths for nicer display."""
    try:
        path = Path(full_path)
        temp_index = next((i for i, part in enumerate(path.parts) if part.startswith('tmp')), None)
        return '/'.join(path.parts[temp_index + 1:]) if temp_index is not None else str(path)
    except Exception as e:
        logger.error(f"Error cleaning path {full_path}: {str(e)}")
        return str(full_path)


def get_gemini_suggestion(finding: dict, max_retries: int = 3, delay: int = 2) -> str:
    """Ask Gemini for a brief, manual fix suggestion for a Semgrep finding."""
    prompt = (
        f"Issue found by Semgrep:\n"
        f"- Rule ID: {finding.get('check_id')}\n"
        f"- Message: {finding.get('message')}\n"
        f"- File: {finding.get('file_path')}\n"
        f"- Line: {finding.get('file_line_range')}\n"
        f"- Code: {finding.get('code')}\n"
        f"- Severity: {finding.get('severity', 'Unknown')}\n\n"
        f"Give a short manual improvement suggestion. Do not propose auto-fixes."
    )
    for attempt in range(max_retries):
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            return (response.text or "").strip()
        except Exception as e:
            logger.warning(f"Gemini error on attempt {attempt + 1}: {e}")
            time.sleep(delay)
    return "Review this finding and apply best practices."



def run_semgrep(target_path: str) -> dict:
    """Run Semgrep and return normalized results (failed list + summary)."""
    cmd = ["semgrep", "scan", target_path, "--config=auto", "--json"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        output = proc.stdout.strip()
        if not output:
            return {"status": "success", "results": {"failed_checks": [], "summary": {"failed": 0}}}

        data = json.loads(output)
        findings = data.get("results", [])
        enriched = []

        for f in findings:
            try:
                suggestion = get_gemini_suggestion({
                    "check_id": f.get("check_id"),
                    "message": f.get("extra", {}).get("message"),
                    "file_path": f.get("path"),
                    "file_line_range": [
                        f.get("start", {}).get("line", 0),
                        f.get("end", {}).get("line", 0)
                    ],
                    "code": f.get("extra", {}).get("lines", ""),
                    "severity": f.get("extra", {}).get("severity", "UNKNOWN")
                })
            except Exception:
                suggestion = "Review this finding and apply best practices."

            enriched.append({
                "check_id": f.get("check_id"),
                "message": f.get("extra", {}).get("message"),
                "file_path": clean_path(f.get("path")),
                "file_line_range": [
                    f.get("start", {}).get("line", 0),
                    f.get("end", {}).get("line", 0)
                ],
                "severity": f.get("extra", {}).get("severity", "UNKNOWN"),
                "code": f.get("extra", {}).get("lines", ""),
                "suggestion": suggestion
            })
            time.sleep(1)  # be gentle with Gemini

        return {
            "status": "failed" if enriched else "success",
            "results": {
                "failed_checks": enriched,
                "summary": {"failed": len(enriched)}
            }
        }

    except subprocess.TimeoutExpired:
        raise RuntimeError("Semgrep scan timed out")
    except Exception as e:
        raise RuntimeError(f"Semgrep failed: {str(e)}")



def save_scan_history(user_id, result, input_type, repo_url=None):
    """Persist Semgrep results and send one HTML email (with CSV) — English, no emojis, no scan id in subject."""
    try:
        # Save ScanHistory
        scan = ScanHistory(
            user_id=user_id,
            repo_url=repo_url,
            scan_result=result,
            status=result.get("status"),
            score=100 if result.get("results", {}).get("summary", {}).get("failed") == 0 else 0,
            compliant=result.get("results", {}).get("summary", {}).get("failed") == 0,
            input_type=input_type,
            scan_type="semgrep",
        )
        db.session.add(scan)
        db.session.flush()
        scan_id = scan.id
        db.session.commit()
        logger.info(f"Saved Semgrep scan with ID {scan_id}")

        # Single combined email (HTML + CSV)
        try:
            csv_path, csv_filename = generate_csv_for_scan(scan_id)
            user = db.session.get(User, int(user_id))

            repo_disp = (repo_url or "local").rstrip("/").split("/")[-1]
            findings = int((result.get("results", {}) or {}).get("summary", {}).get("failed", 0) or 0)
            final_status = "SUCCESS" if findings == 0 else "FAILED"
            status_color = "#16a34a" if final_status == "SUCCESS" else "#dc2626"

            subject = f"SafeOps — Semgrep: Scan completed for {repo_disp}"
            # No executed_at; no scan id
            body = (
                f"<strong>Status:</strong> "
                f"<span style='color:{status_color};font-weight:600;'>{final_status}</span><br>"
                f"<strong>Findings:</strong> {findings}<br>"
                f"<strong>Repository/path:</strong> {repo_disp}"
            )

            if user:
                send_csv_report_email(
                    to_email=user.email,
                    subject=subject,
                    body_text=body,
                    csv_path=csv_path,
                    csv_filename=csv_filename,
                    user_name=user.name,
                )
        except Exception as e:
            logger.warning(f"Combined email (finish + CSV) failed for Semgrep scan_id {scan_id}: {e}")

        return scan_id

    except Exception as e:
        logger.error(f"Failed to save scan for user_id {user_id}: {str(e)}")
        db.session.rollback()
        raise RuntimeError(f"Failed to save scan: {str(e)}")

def validate_semgrep(user_id, input_type, file=None, repo_url=None, content=None, extension="py"):
    """
    Validate inputs and run Semgrep. Returns {"scan_id": id, **result}.
    input_type: "file" | "zip" | "repo" | "content"
    """
    if not user_id:
        raise ValueError("user_id is required")

    temp_dir = tempfile.mkdtemp()
    try:
        if input_type == "file" and file:
            file_path = os.path.join(temp_dir, file.filename)
            file.save(file_path)
            result = run_semgrep(file_path)
            scan_id = save_scan_history(user_id, result, input_type)
            return {"scan_id": scan_id, **result}

        elif input_type == "zip" and file:
            zip_path = os.path.join(temp_dir, file.filename)
            file.save(zip_path)
            extract_path = os.path.join(temp_dir, "extracted")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            result = run_semgrep(extract_path)
            scan_id = save_scan_history(user_id, result, input_type)
            return {"scan_id": scan_id, **result}

        elif input_type == "repo" and repo_url:
            clone_path = os.path.join(temp_dir, "repo")
            logger.debug(f"Cloning {repo_url} into {clone_path}")
            Repo.clone_from(repo_url, clone_path, depth=1)
            result = run_semgrep(clone_path)
            scan_id = save_scan_history(user_id, result, input_type, repo_url=repo_url)
            return {"scan_id": scan_id, **result}

        elif input_type == "content" and content:
            file_path = os.path.join(temp_dir, f"input.{extension}")
            with open(file_path, "w") as f:
                f.write(content)
            result = run_semgrep(file_path)
            scan_id = save_scan_history(user_id, result, input_type)
            return {"scan_id": scan_id, **result}

        raise ValueError("Invalid input_type or missing required data")

    except Exception as e:
        logger.error(f"Error processing Semgrep scan for user_id {user_id}: {str(e)}")
        raise RuntimeError(str(e))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
