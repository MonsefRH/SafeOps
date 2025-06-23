from pathlib import Path
from flask import Blueprint, request, jsonify
import os
import tempfile
import zipfile
import subprocess
import shutil
import json
import logging
import time
import google.generativeai as genai
from google.api_core import exceptions
from psycopg2.extras import Json

from utils.db import get_db_connection

semgrep_bp = Blueprint('semgrep', __name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s:%(name)s: %(message)s',
    handlers=[
        logging.FileHandler('semgrep_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY environment variable not set.")
    raise ValueError("GEMINI_API_KEY environment variable not set.")
genai.configure(api_key=GEMINI_API_KEY)

def clean_path(full_path):
    try:
        path = Path(full_path)
        temp_index = next((i for i, part in enumerate(path.parts) if part.startswith('tmp')), None)
        return '/'.join(path.parts[temp_index + 1:]) if temp_index is not None else str(path)
    except Exception as e:
        logger.error(f"Error cleaning path {full_path}: {str(e)}")
        return str(full_path)

def get_gemini_suggestion(finding, max_retries=3, delay=2):
    prompt = (
        f"Issue found by Semgrep:\n"
        f"- Rule ID: {finding.get('check_id')}\n"
        f"- Message: {finding.get('message')}\n"
        f"- File: {finding.get('file_path')}\n"
        f"- Line: {finding.get('file_line_range')}\n"
        f"- Code: {finding.get('code')}\n"
        f"- Severity: {finding.get('severity', 'Unknown')}\n\n"
        f"Give a manual improvement suggestion. Don't auto-fix the code."
    )
    for attempt in range(max_retries):
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.warning(f"Gemini error on attempt {attempt+1}: {e}")
            time.sleep(delay)
    return "Unable to get suggestion from Gemini."

def run_semgrep(target_path):
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
                "suggestion": get_gemini_suggestion({
                    "check_id": f.get("check_id"),
                    "message": f.get("extra", {}).get("message"),
                    "file_path": f.get("path"),
                    "file_line_range": [f.get("start", {}).get("line", 0), f.get("end", {}).get("line", 0)],
                    "code": f.get("extra", {}).get("lines", ""),
                    "severity": f.get("extra", {}).get("severity", "UNKNOWN")
                })
            })
            time.sleep(1)
        return {
            "status": "failed" if enriched else "success",
            "results": {
                "failed_checks": enriched,
                "summary": {"failed": len(enriched)}
            }
        }
    except Exception as e:
        logger.error(f"Semgrep failed: {e}")
        return {"status": "error", "message": str(e)}

def save_scan_history(user_id, result, input_type, repo_url=None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO scan_history (user_id, repo_url, scan_result, status, score, compliant, input_type, scan_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            """,
            (
                user_id,
                repo_url,
                Json(result),
                result.get("status"),
                100 if result.get("results", {}).get("summary", {}).get("failed") == 0 else 0,
                result.get("results", {}).get("summary", {}).get("failed") == 0,
                input_type,
                "semgrep"
            )
        )
        conn.commit()
        scan_id = cursor.fetchone()[0]
        logger.info(f"Saved Semgrep scan with ID {scan_id}")
        return scan_id
    except Exception as e:
        logger.error(f"Failed to save scan: {str(e)}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

@semgrep_bp.route("/semgrep", methods=["POST"])
def validate_semgrep():
    input_type = request.form.get("input_type")
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    temp_dir = tempfile.mkdtemp()
    try:
        if input_type == "file" and "file" in request.files:
            file = request.files["file"]
            file_path = os.path.join(temp_dir, file.filename)
            file.save(file_path)
            result = run_semgrep(file_path)
            save_scan_history(user_id, result, input_type)
            return jsonify(result)

        elif input_type == "zip" and "file" in request.files:
            file = request.files["file"]
            zip_path = os.path.join(temp_dir, file.filename)
            file.save(zip_path)
            extract_path = os.path.join(temp_dir, "extracted")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            result = run_semgrep(extract_path)
            save_scan_history(user_id, result, input_type)
            return jsonify(result)

        elif input_type == "repo":
            repo_url = request.form.get("repo_url")
            if not repo_url:
                return jsonify({"error": "repo_url required"}), 400
            clone_path = os.path.join(temp_dir, "repo")
            subprocess.run(["git", "clone", "--depth", "1", repo_url, clone_path], check=True)
            result = run_semgrep(clone_path)
            save_scan_history(user_id, result, input_type, repo_url=repo_url)
            return jsonify(result)

        elif input_type == "file" and request.form.get("content"):
            content = request.form["content"]
            ext = request.form.get("extension", "py")
            file_path = os.path.join(temp_dir, f"input.{ext}")
            with open(file_path, "w") as f:
                f.write(content)
            result = run_semgrep(file_path)
            save_scan_history(user_id, result, "content")
            return jsonify(result)

        return jsonify({"error": "Invalid input_type or missing file"}), 400
    except Exception as e:
        logger.error(f"Error in /semgrep: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
def run_semgrep_scan(path, user_id, input_type="repo", repo_url=None):
    result = run_semgrep(path)
    save_scan_history(user_id, result, input_type, repo_url)
    return result