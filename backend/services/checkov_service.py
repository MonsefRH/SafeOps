# services/checkov_service.py
from pathlib import Path
import os
import tempfile
import zipfile
import subprocess
import shutil
import stat
import json
import logging
import time
from datetime import datetime

import google.generativeai as genai
from google.api_core import exceptions

from utils.db import db
from models.selected_repo import SelectedRepo
from models.scan_history import ScanHistory
from models.file_content import FileContent
from models.user import User

# CSV report + HTML email wrapper
from services.report_service import generate_csv_for_scan, send_csv_report_email

logger = logging.getLogger(__name__)

# -------- Gemini ----------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY environment variable not set.")
    raise ValueError("GEMINI_API_KEY environment variable not set.")
genai.configure(api_key=GEMINI_API_KEY)

ENABLE_AI_SUGGESTIONS = os.getenv("ENABLE_AI_SUGGESTIONS", "true").lower() == "true"

# Cache for checkov path
_checkov_path = None


def clean_path(full_path: str) -> str:
    """Remove temp-dir prefixes from file paths for nicer display."""
    try:
        path = Path(full_path)
        temp_index = next((i for i, part in enumerate(path.parts) if part.startswith('tmp')), None)
        if temp_index is not None:
            return '/'.join(path.parts[temp_index + 1:])
        logger.warning(f"Temporary directory not found in path: {full_path}")
        return str(path)
    except Exception as e:
        logger.error(f"Error cleaning path {full_path}: {str(e)}")
        return str(full_path)


def get_checkov_path() -> str:
    """Resolve the Checkov executable path."""
    global _checkov_path
    if _checkov_path:
        return _checkov_path

    checkov_path = shutil.which("checkov.exe")
    if checkov_path and os.path.exists(checkov_path):
        _checkov_path = checkov_path
        return _checkov_path

    fallback_path = os.getenv("CHECKOV_FILE_PATH")
    if fallback_path and os.path.exists(fallback_path):
        _checkov_path = fallback_path
        return _checkov_path

    _checkov_path = "checkov"  # fallback to PATH
    return _checkov_path


def get_gemini_suggestion(check: dict, max_retries: int = 3, retry_delay: int = 5) -> str:
    """Ask Gemini for a short manual suggestion for a Checkov finding."""
    prompt = (
        f"I have detected an issue in an Infrastructure-as-Code file using Checkov.\n"
        f"- Check ID: {check.get('check_id')}\n"
        f"- Check Name: {check.get('check_name')}\n"
        f"- File Path: {check.get('file_path')}\n"
        f"- Line Range: {check.get('file_line_range')}\n"
        f"- Resource: {check.get('resource')}\n"
        f"- Severity: {check.get('severity') or 'Unknown'}\n"
        f"Provide a concise improvement suggestion (manual, no auto-fix)."
    )

    # Fast path if AI suggestions disabled
    if not ENABLE_AI_SUGGESTIONS:
        start, end = (check.get("file_line_range") or [0, 0])[:2]
        return (f"Review {check.get('check_name')} in {check.get('file_path')} "
                f"(lines {start}-{end}) and apply best practices.")

    for attempt in range(max_retries):
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            suggestion = (response.text or "").strip()
            if suggestion:
                return suggestion
        except exceptions.ResourceExhausted:
            time.sleep(retry_delay)
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)

    start, end = (check.get("file_line_range") or [0, 0])[:2]
    return (f"Review {check.get('check_name')} in {check.get('file_path')} "
            f"(lines {start}-{end}) and apply best practices.")


def detect_framework(file_path: str) -> str | None:
    if file_path.endswith(('.yaml', '.yml')):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'apiVersion' in content and 'kind' in content:
                    return 'kubernetes'
        except Exception:
            pass
        return 'kubernetes'
    if file_path.endswith('.tf'):
        return 'terraform'
    if os.path.basename(file_path) == 'Dockerfile':
        return 'dockerfile'
    return None


def run_checkov_on_single_file(file_path: str) -> dict:
    """Run Checkov on one file and normalize the output."""
    if not os.path.exists(file_path):
        return {
            "status": "error",
            "message": f"Le fichier {clean_path(file_path)} n'existe pas",
            "passed_checks": [],
            "failed_checks": [],
            "summary": {"passed": 0, "failed": 0}
        }

    framework = detect_framework(file_path)
    if not framework:
        return {
            "status": "error",
            "message": "Type de fichier non supporté",
            "passed_checks": [],
            "failed_checks": [],
            "summary": {"passed": 0, "failed": 0}
        }

    checkov_path = get_checkov_path()
    cmd = [checkov_path, "-f", file_path, "--framework", framework, "-o", "json", "--quiet"]

    try:
        # Windows exe vs PATH
        if checkov_path == "checkov":
            process = subprocess.run(' '.join(cmd), shell=True, capture_output=True, text=True, timeout=60)
        else:
            process = subprocess.run(cmd, shell=False, capture_output=True, text=True, timeout=60)

        if not process.stdout.strip():
            return {
                "status": "no_output",
                "passed_checks": [],
                "failed_checks": [],
                "summary": {"passed": 0, "failed": 0}
            }

        try:
            output = json.loads(process.stdout)

            if isinstance(output, dict):
                results = output.get("results", {})
                failed = results.get("failed_checks", [])
                passed = results.get("passed_checks", [])
            elif isinstance(output, list):
                failed = [r for r in output if r.get("check_result", {}).get("result") == "FAILED"]
                passed = [r for r in output if r.get("check_result", {}).get("result") == "PASSED"]
            else:
                failed, passed = [], []

            filtered_failed = []
            for item in failed:
                try:
                    suggestion = get_gemini_suggestion({
                        "check_id": item.get("check_id"),
                        "check_name": item.get("check_name"),
                        "file_path": clean_path(file_path),
                        "file_line_range": item.get("file_line_range"),
                        "resource": item.get("resource"),
                        "severity": item.get("severity")
                    })
                except Exception:
                    suggestion = "Review this finding and apply best practices."

                filtered_failed.append({
                    "check_id": item.get("check_id"),
                    "check_name": item.get("check_name"),
                    "file_path": clean_path(file_path),
                    "guideline": item.get("guideline"),
                    "file_line_range": item.get("file_line_range"),
                    "resource": item.get("resource"),
                    "severity": item.get("severity"),
                    "suggestion": suggestion
                })

                if ENABLE_AI_SUGGESTIONS:
                    time.sleep(1)

            filtered_passed = [{
                "check_id": item.get("check_id"),
                "check_name": item.get("check_name"),
                "file_path": clean_path(file_path),
                "file_line_range": item.get("file_line_range"),
                "resource": item.get("resource")
            } for item in passed]

            total_passed = len(filtered_passed)
            total_failed = len(filtered_failed)
            total_checks = total_passed + total_failed
            score = round((total_passed / total_checks) * 100) if total_checks > 0 else 0

            return {
                "status": "success",
                "path_scanned": clean_path(file_path),
                "files_found": [clean_path(file_path)],
                "passed_checks": filtered_passed,
                "failed_checks": filtered_failed,
                "summary": {"passed": total_passed, "failed": total_failed},
                "score": score,
                "compliant": score == 100,
                "raw_output": output
            }

        except json.JSONDecodeError:
            return {
                "status": "json_error",
                "passed_checks": [],
                "failed_checks": [],
                "summary": {"passed": 0, "failed": 0},
                "stdout": process.stdout[:500]
            }

    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "message": "Checkov command timed out after 60 seconds",
            "passed_checks": [],
            "failed_checks": [],
            "summary": {"passed": 0, "failed": 0}
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "passed_checks": [],
            "failed_checks": [],
            "summary": {"passed": 0, "failed": 0}
        }


def run_checkov_on_dir(path: str, is_file: bool = False) -> dict:
    """Run Checkov on a directory (or delegate to single-file)."""
    if is_file:
        return run_checkov_on_single_file(path)

    if not os.path.exists(path):
        return {
            "status": "error",
            "message": f"Le chemin {path} n'existe pas",
            "passed_checks": [],
            "failed_checks": [],
            "summary": {"passed": 0, "failed": 0}
        }

    files_found = []
    for root, _, files in os.walk(path):
        for file in files:
            fp = os.path.join(root, file)
            if file.endswith(('.tf', '.yaml', '.yml')) or file == 'Dockerfile':
                files_found.append(fp)

    if not files_found:
        return {
            "status": "error",
            "message": "Aucun fichier scannable trouvé",
            "passed_checks": [],
            "failed_checks": [],
            "summary": {"passed": 0, "failed": 0}
        }

    results = {
        "status": "completed",
        "path_scanned": clean_path(path),
        "files_found": [clean_path(f) for f in files_found],
        "passed_checks": [],
        "failed_checks": [],
        "summary": {"passed": 0, "failed": 0}
    }

    total_passed = 0
    total_failed = 0
    for fp in files_found:
        r = run_checkov_on_single_file(fp)
        total_passed += len(r.get("passed_checks", []))
        total_failed += len(r.get("failed_checks", []))
        results["failed_checks"].extend(r.get("failed_checks", []))
        results["passed_checks"].extend(r.get("passed_checks", []))

    results["summary"]["passed"] = total_passed
    results["summary"]["failed"] = total_failed
    total_checks = total_passed + total_failed
    results["score"] = round((total_passed / total_checks) * 100) if total_checks > 0 else 0
    results["compliant"] = results["score"] == 100
    return results


def save_file_contents(scan_id: int, files: list[tuple[str, str]], input_type: str) -> None:
    """Persist captured file contents used in a scan."""
    try:
        for file_path, content in files:
            file_content = FileContent(
                scan_id=scan_id,
                file_path=file_path,
                content=content,
                input_type=input_type
            )
            db.session.add(file_content)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def _repo_display(repo_url: str | None, fallback: str) -> str:
    if repo_url:
        parts = repo_url.rstrip("/").split("/")
        return f"{parts[-2]}/{parts[-1]}" if len(parts) >= 2 else parts[-1]
    return fallback


def _final_status(result: dict) -> str:
    status_raw = (result.get("status") or "").lower()
    failed = int(result.get("summary", {}).get("failed", 0) or 0)
    if status_raw in {"error", "timeout", "json_error"}:
        return "FAILED"
    return "FAILED" if failed > 0 else "SUCCESS"


def save_scan_history(user_id, result, input_type, repo_url=None, files_to_save=None):
    """
    Persist Checkov results, optional file contents, and send ONE HTML email with CSV attached.
    Email is in English, no emojis, and **no scan ID** in the subject.
    """
    try:
        # Resolve / create repo entry
        repo_id = None
        if repo_url:
            repo_name = repo_url.split("/")[-2] + "/" + repo_url.split("/")[-1]
            repo = SelectedRepo.query.filter_by(full_name=repo_name).first()
            if repo:
                repo_id = repo.id
            else:
                repo = SelectedRepo(user_id=user_id, full_name=repo_name, html_url=repo_url)
                db.session.add(repo)
                db.session.flush()
                repo_id = repo.id

        # Normalize result
        if result.get("files_found"):
            result["files_found"] = [f.replace("\\", "/") for f in result["files_found"]]
        if not result.get("path_scanned"):
            result["path_scanned"] = clean_path(tempfile.gettempdir())

        # Persist ScanHistory
        scan_history = ScanHistory(
            user_id=user_id,
            repo_id=repo_id,
            scan_result=result,
            repo_url=repo_url,
            status=result.get("status", "unknown"),
            score=result.get("score"),
            compliant=result.get("compliant"),
            input_type=input_type,
            scan_type="checkov",
        )
        db.session.add(scan_history)
        db.session.flush()
        scan_id = scan_history.id
        db.session.commit()

        # Save file contents if provided
        if files_to_save:
            save_file_contents(scan_id, files_to_save, input_type)

        # ---- ONE combined HTML email with CSV (no emojis, no scan id) ----
        try:
            csv_path, csv_filename = generate_csv_for_scan(scan_id)
            user = db.session.get(User, int(user_id))

            repo_disp = _repo_display(repo_url, result.get("path_scanned", "local"))
            findings = int(result.get("summary", {}).get("failed", 0) or 0)
            final_status = _final_status(result)
            status_color = "#16a34a" if final_status == "SUCCESS" else "#dc2626"

            subject = f"SafeOps — Checkov: Scan completed for {repo_disp}"
            # Note: send_csv_report_email wraps this HTML fragment inside the blue template.
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
            logger.warning(f"Combined email (finish + CSV) failed for scan_id {scan_id}: {e}")

        return scan_id

    except Exception as e:
        logger.error(f"Failed to save scan history: {str(e)}")
        db.session.rollback()
        raise


def run_checkov_scan(user_id, input_type, content=None, file_path=None, repo_url=None, zip_path=None):
    """Entry point used by routes to run a Checkov scan and persist it."""
    temp_dir = None
    files_to_save = []
    try:
        if input_type == "content":
            if not content:
                raise ValueError("Content is required for content input type")
            framework = "terraform"
            extension = {"terraform": ".tf", "kubernetes": ".yaml", "dockerfile": "Dockerfile"}.get(framework, ".tf")

            temp_dir = tempfile.mkdtemp()
            temp_file_path = os.path.join(temp_dir, "Dockerfile" if extension == "Dockerfile" else f"input{extension}")
            with open(temp_file_path, "w", encoding="utf-8") as f:
                f.write(content)

            result = run_checkov_on_single_file(temp_file_path)
            result.setdefault("meta", {})
            result["meta"]["executed_at"] = datetime.utcnow().isoformat() + "Z"

            files_to_save = [(clean_path(temp_file_path), content)]
            scan_id = save_scan_history(user_id, result, input_type, files_to_save=files_to_save)
            return {"scan_id": scan_id, "results": result}

        elif input_type == "file":
            if not file_path or not os.path.exists(file_path):
                raise ValueError(f"Le fichier {file_path} n'existe pas")

            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()

            result = run_checkov_on_dir(file_path, is_file=True)
            result.setdefault("meta", {})
            result["meta"]["executed_at"] = datetime.utcnow().isoformat() + "Z"

            files_to_save = [(clean_path(file_path), file_content)]
            scan_id = save_scan_history(user_id, result, input_type, files_to_save=files_to_save)
            return {"scan_id": scan_id, "results": result}

        elif input_type == "zip":
            if not zip_path or not os.path.exists(zip_path):
                raise ValueError("Le fichier ZIP est invalide")

            temp_dir = tempfile.mkdtemp()
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)

            macosx_path = os.path.join(temp_dir, "__MACOSX")
            if os.path.exists(macosx_path):
                shutil.rmtree(macosx_path)

            files_found = []
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    p = os.path.join(root, file)
                    if file.endswith(('.tf', '.yaml', '.yml')) or file == 'Dockerfile':
                        with open(p, "r", encoding="utf-8") as f:
                            content = f.read()
                        files_found.append((clean_path(p), content))

            if not files_found:
                raise ValueError("Aucun fichier scannable trouvé dans l’archive")

            result = run_checkov_on_dir(temp_dir, is_file=False)
            result.setdefault("meta", {})
            result["meta"]["executed_at"] = datetime.utcnow().isoformat() + "Z"

            scan_id = save_scan_history(user_id, result, input_type, files_to_save=files_found)
            return {"scan_id": scan_id, "results": result}

        elif input_type == "repo":
            if not repo_url:
                raise ValueError("repo_url est requis")

            temp_dir = tempfile.mkdtemp()
            clone_cmd = ["git", "clone", "--depth", "1", repo_url, temp_dir]
            subprocess.run(clone_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            # make directory deletable on Windows
            git_dir = os.path.join(temp_dir, ".git")
            if os.path.exists(git_dir):
                def remove_readonly(func, path, _):
                    os.chmod(path, stat.S_IWRITE)
                    func(path)
                shutil.rmtree(git_dir, onerror=remove_readonly)

            files_found = []
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    p = os.path.join(root, file)
                    if file.endswith(('.tf', '.yaml', '.yml')) or file == 'Dockerfile':
                        with open(p, "r", encoding="utf-8") as f:
                            content = f.read()
                        files_found.append((clean_path(p), content))

            if not files_found:
                raise ValueError("Aucun fichier scannable trouvé dans le dépôt")

            result = run_checkov_on_dir(temp_dir, is_file=False)
            result.setdefault("meta", {})
            result["meta"]["executed_at"] = datetime.utcnow().isoformat() + "Z"

            scan_id = save_scan_history(user_id, result, input_type, repo_url=repo_url, files_to_save=files_found)
            return {"scan_id": scan_id, "results": result}

        raise ValueError("Type d'entrée invalide. Utilisez 'file', 'zip', 'repo' ou 'content'")

    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
