from pathlib import Path
from flask import Blueprint, request, jsonify
import os
import tempfile
import zipfile
import subprocess
import shutil
import stat
import json
import logging
import time
import google.generativeai as genai
from google.api_core import exceptions
from psycopg2.extras import Json

from utils.db import get_db_connection

checkov_bp = Blueprint('checkov', __name__)

# Configure upload folder
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configure logging to file and console
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s:%(name)s: %(message)s',
    handlers=[
        logging.FileHandler('checkov_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY environment variable not set.")
    raise ValueError("GEMINI_API_KEY environment variable not set.")
genai.configure(api_key=GEMINI_API_KEY)

# Cache the Checkov path globally
_checkov_path = None

def clean_path(full_path):
    """Remove temporary directory prefix from file paths."""
    try:
        path = Path(full_path)
        temp_index = next((i for i, part in enumerate(path.parts) if part.startswith('tmp')), None)
        if temp_index is not None:
            relative_path = '/'.join(path.parts[temp_index + 1:])
            return relative_path
        logger.warning(f"Temporary directory not found in path: {full_path}")
        return str(path)
    except Exception as e:
        logger.error(f"Error cleaning path {full_path}: {str(e)}")
        return str(full_path)

def get_checkov_path():
    global _checkov_path
    if _checkov_path:
        return _checkov_path

    checkov_path = shutil.which("checkov.exe")
    if checkov_path and os.path.exists(checkov_path):
        logger.info(f"Found Checkov executable at {checkov_path}")
        _checkov_path = checkov_path
        return _checkov_path

    fallback_path = os.getenv("CHECKOV_FILE_PATH")
    if fallback_path and os.path.exists(fallback_path):
        logger.info(f"Found Checkov executable at fallback path {fallback_path}")
        _checkov_path = fallback_path
        return _checkov_path

    logger.warning("Falling back to shell execution with 'checkov' as checkov.exe not found")
    _checkov_path = "checkov"
    return _checkov_path

def get_gemini_suggestion(check, max_retries=3, retry_delay=5):
    prompt = (
        f"I have detected an issue in an Infrastructure-as-Code file using Checkov. "
        f"Here are the details:\n"
        f"- Check ID: {check['check_id']}\n"
        f"- Check Name: {check['check_name']}\n"
        f"- File Path: {check['file_path']}\n"
        f"- Line Range: {check['file_line_range']}\n"
        f"- Resource: {check['resource']}\n"
        f"- Severity: {check['severity'] or 'Unknown'}\n"
        f"Please provide a concise suggestion for improving this issue. "
        f"Do not suggest automatic fixes, only recommend manual improvements."
    )

    for attempt in range(max_retries):
        try:
            logger.debug(f"Attempt {attempt + 1}/{max_retries} - Sending prompt to Gemini for check {check['check_id']}: {prompt[:100]}...")
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            suggestion = response.text.strip()
            logger.debug(f"Gemini suggestion for {check['check_id']}: {suggestion}")
            return suggestion
        except exceptions.ResourceExhausted:
            logger.warning(f"Rate limit hit for check {check['check_id']}, attempt {attempt + 1}/{max_retries}. Retrying after {retry_delay}s...")
            time.sleep(retry_delay)
        except Exception as e:
            logger.error(f"Failed to get Gemini suggestion for check {check['check_id']}, attempt {attempt + 1}/{max_retries}: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            continue
    logger.error(f"All {max_retries} attempts failed for check {check['check_id']}.")
    return f"Review the {check['check_name']} issue in {check['file_path']} (lines {check['file_line_range'][0]}-{check['file_line_range'][1]}) and apply best practices to address it."

def detect_framework(file_path):
    if file_path.endswith(('.yaml', '.yml')):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'apiVersion' in content and 'kind' in content:
                    return 'kubernetes'
        except Exception as e:
            logger.warning(f"Could not read file {file_path} for framework detection: {str(e)}")
        return 'kubernetes'
    elif file_path.endswith('.tf'):
        return 'terraform'
    elif os.path.basename(file_path) == 'Dockerfile':
        return 'dockerfile'
    return None

def run_checkov_on_single_file(file_path):
    if not os.path.exists(file_path):
        return {
            "results": {
                "status": "error",
                "message": f"Le fichier {clean_path(file_path)} n'existe pas",
                "passed_checks": [],
                "failed_checks": [],
                "summary": {"passed": 0, "failed": 0}
            }
        }

    framework = detect_framework(file_path)
    if not framework:
        return {
            "results": {
                "status": "error",
                "message": "Type de fichier non supporté",
                "passed_checks": [],
                "failed_checks": [],
                "summary": {"passed": 0, "failed": 0}
            }
        }

    checkov_path = get_checkov_path()
    cmd = [
        checkov_path,
        "-f", file_path,
        "--framework", framework,
        "-o", "json",
        "--quiet"
    ]

    try:
        logger.debug(f"Executing Checkov command on single file: {' '.join(cmd)}")
        if checkov_path == "checkov":
            process = subprocess.run(' '.join(cmd), shell=True, capture_output=True, text=True, timeout=60)
        else:
            process = subprocess.run(cmd, shell=False, capture_output=True, text=True, timeout=60)

        if not process.stdout.strip():
            logger.warning(f"Checkov produced no output for {file_path}")
            return {
                "results": {
                    "status": "no_output",
                    "passed_checks": [],
                    "failed_checks": [],
                    "summary": {"passed": 0, "failed": 0}
                }
            }

        try:
            output = json.loads(process.stdout)
            logger.debug(f"Checkov output for {file_path}: {json.dumps(output, indent=2)[:500]}...")

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
                issue = {
                    "check_id": item.get("check_id"),
                    "check_name": item.get("check_name"),
                    "file_path": clean_path(file_path),
                    "guideline": item.get("guideline"),
                    "file_line_range": item.get("file_line_range"),
                    "resource": item.get("resource"),
                    "severity": item.get("severity"),
                    "suggestion": get_gemini_suggestion({
                        "check_id": item.get("check_id"),
                        "check_name": item.get("check_name"),
                        "file_path": clean_path(file_path),
                        "file_line_range": item.get("file_line_range"),
                        "resource": item.get("resource"),
                        "severity": item.get("severity")
                    })
                }
                filtered_failed.append(issue)
                time.sleep(1)

            filtered_passed = [
                {
                    "check_id": item.get("check_id"),
                    "check_name": item.get("check_name"),
                    "file_path": clean_path(file_path),
                    "file_line_range": item.get("file_line_range"),
                    "resource": item.get("resource")
                }
                for item in passed
            ]

            total_passed = len(filtered_passed)
            total_failed = len(filtered_failed)
            total_checks = total_passed + total_failed
            score = round((total_passed / total_checks) * 100) if total_checks > 0 else 0

            result = {
                "results": {
                    "status": "success",
                    "path_scanned": clean_path(file_path),
                    "files_found": [clean_path(file_path)],
                    "passed_checks": filtered_passed,
                    "failed_checks": filtered_failed,
                    "summary": {"passed": total_passed, "failed": total_failed},
                    "score": score,
                    "compliant": score == 100
                }
            }
            logger.debug(f"Single file result for {file_path}: {json.dumps(result, indent=2)[:500]}...")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Checkov JSON output for {file_path}: {process.stdout}, Error: {str(e)}")
            return {
                "results": {
                    "status": "json_error",
                    "passed_checks": [],
                    "failed_checks": [],
                    "summary": {"passed": 0, "failed": 0},
                    "stdout": process.stdout[:500]
                }
            }

    except subprocess.TimeoutExpired:
        logger.error(f"Checkov command timed out after 60 seconds for {file_path}")
        return {
            "results": {
                "status": "timeout",
                "message": "Checkov command timed out after 60 seconds",
                "passed_checks": [],
                "failed_checks": [],
                "summary": {"passed": 0, "failed": 0}
            }
        }
    except Exception as e:
        logger.error(f"Unexpected error running Checkov on {file_path}: {str(e)}")
        return {
            "results": {
                "status": "error",
                "message": str(e),
                "passed_checks": [],
                "failed_checks": [],
                "summary": {"passed": 0, "failed": 0}
            }
        }

def run_checkov_on_dir(path, is_file=False):
    if is_file:
        return run_checkov_on_single_file(path)

    if not os.path.exists(path):
        return {
            "results": {
                "status": "error",
                "message": f"Le chemin {path} n'existe pas",
                "passed_checks": [],
                "failed_checks": [],
                "summary": {"passed": 0, "failed": 0}
            }
        }

    files_found = []
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith(('.tf', '.yaml', '.yml')) or file == 'Dockerfile':
                files_found.append(file_path)

    if not files_found:
        return {
            "results": {
                "status": "error",
                "message": "Aucun fichier scannable trouvé",
                "passed_checks": [],
                "failed_checks": [],
                "summary": {"passed": 0, "failed": 0}
            }
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

    for file_path in files_found:
        file_result = run_checkov_on_single_file(file_path)
        file_results = file_result.get("results", {})
        logger.debug(f"Processing file {file_path}: {json.dumps(file_results, indent=2)[:500]}...")
        total_passed += len(file_results.get("passed_checks", []))
        total_failed += len(file_results.get("failed_checks", []))
        results["failed_checks"].extend(file_results.get("failed_checks", []))
        results["passed_checks"].extend(file_results.get("passed_checks", []))

    results["summary"]["passed"] = total_passed
    results["summary"]["failed"] = total_failed
    total_checks = total_passed + total_failed
    results["score"] = round((total_passed / total_checks) * 100) if total_checks > 0 else 0
    results["compliant"] = results["score"] == 100

    logger.debug(f"Final directory scan result: {json.dumps(results, indent=2)[:1000]}...")
    return {"results": results}

def save_file_contents(scan_id, files, input_type):
    """Save the content of files to the file_contents table."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        for file_path, content in files:
            cursor.execute(
                """
                INSERT INTO file_contents (scan_id, file_path, content, input_type)
                VALUES (%s, %s, %s, %s)
                """,
                (scan_id, file_path, content, input_type)
            )

        conn.commit()
        logger.info(f"Saved {len(files)} file contents for scan_id {scan_id}")
    except Exception as e:
        logger.error(f"Failed to save file contents for scan_id {scan_id}: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def save_scan_history(user_id, result, input_type, repo_url=None, files_to_save=None):
    """Save the scan result and associated file contents to the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        repo_id = None

        if repo_url:
            repo_name = repo_url.split("/")[-2] + "/" + repo_url.split("/")[-1]
            cursor.execute(
                "SELECT id FROM selected_repos WHERE full_name = %s",
                (repo_name,)
            )
            row = cursor.fetchone()
            if row:
                repo_id = row[0]
            else:
                cursor.execute(
                    "INSERT INTO selected_repos (user_id, full_name, html_url) VALUES (%s, %s, %s) RETURNING id",
                    (user_id, repo_name, repo_url)
                )
                repo_id = cursor.fetchone()[0]

        # Normalize paths in files_found
        if result.get("results", {}).get("files_found"):
            result["results"]["files_found"] = [f.replace("\\", "/") for f in result["results"]["files_found"]]
        # Set path_scanned if missing
        if not result.get("results", {}).get("path_scanned"):
            result["results"]["path_scanned"] = clean_path(tempfile.gettempdir())

        # Insert scan history
        cursor.execute(
            """
            INSERT INTO scan_history (user_id, repo_id, scan_result, repo_url, status, score, compliant, input_type,scan_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                user_id,
                repo_id,
                Json(result),
                repo_url,
                result.get("results", {}).get("status", "unknown"),
                result.get("results", {}).get("score"),
                result.get("results", {}).get("compliant"),
                input_type,
                "checkov"
            )
        )

        scan_id = cursor.fetchone()[0]



        conn.commit()
        # Save file contents if provided
        if files_to_save:
            save_file_contents(scan_id, files_to_save, input_type)
        logger.info(f"Scan history saved for user_id {user_id} with scan_id {scan_id}")
        return scan_id
    except Exception as e:
        logger.error(f"Failed to save scan history: {str(e)}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

@checkov_bp.route("/checkov", methods=["POST"])
def validate():
    input_type = request.form.get("input_type")

    # Get user_id from request
    user_id = request.headers.get("X-User-ID") or (request.json and request.json.get("user_id"))
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    # Handle JSON input (code or repo_url)
    if not input_type and request.is_json:
        data = request.get_json()

        if "content" in data:
            framework = data.get("framework", "terraform")
            extension = {
                "terraform": ".tf",
                "kubernetes": ".yaml",
                "dockerfile": "Dockerfile"
            }.get(framework, ".tf")

            temp_dir = tempfile.mkdtemp()
            try:
                if extension == "Dockerfile":
                    temp_file_path = os.path.join(temp_dir, "Dockerfile")
                else:
                    temp_file_path = os.path.join(temp_dir, f"input{extension}")

                with open(temp_file_path, "w", encoding="utf-8") as f:
                    f.write(data["content"])

                result = run_checkov_on_single_file(temp_file_path)

                # Save the content of the single file
                files_to_save = [(clean_path(temp_file_path), data["content"])]
                save_scan_history(user_id, result, input_type="content", files_to_save=files_to_save)

                logger.debug(f"Returning result for content input: {json.dumps(result, indent=2)[:500]}...")
                return jsonify(result)
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)

        if "repo_url" in data:
            input_type = "repo"
            request.form = data

    if input_type == "file" and "file" in request.files:
        file = request.files["file"]
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        try:
            file.save(file_path)

            # Read the file content before running Checkov
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()

            result = run_checkov_on_dir(file_path, is_file=True)

            # Save the content of the single file
            files_to_save = [(clean_path(file_path), file_content)]
            save_scan_history(user_id, result, input_type="file", files_to_save=files_to_save)

            logger.debug(f"Returning result for file input: {json.dumps(result, indent=2)[:500]}...")
            return jsonify(result)
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

    elif input_type == "zip" and "file" in request.files:
        file = request.files["file"]
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, file.filename)
        try:
            file.save(zip_path)
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)

            macosx_path = os.path.join(temp_dir, "__MACOSX")
            if os.path.exists(macosx_path):
                shutil.rmtree(macosx_path)

            if not any(f.endswith(('.tf', '.yaml', '.yml')) or f == "Dockerfile" for _, _, files in os.walk(temp_dir) for f in files):
                return jsonify({
                    "results": {
                        "status": "error",
                        "message": "Aucun fichier scannable trouvé dans l’archive",
                        "passed_checks": [],
                        "failed_checks": [],
                        "summary": {"passed": 0, "failed": 0}
                    }
                }), 400

            # Collect the content of all scannable files in the ZIP
            files_to_save = []
            for root, dirs, files in os.walk(temp_dir):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    if file_name.endswith(('.tf', '.yaml', '.yml')) or file_name == 'Dockerfile':
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        files_to_save.append((clean_path(file_path), content))

            result = run_checkov_on_dir(temp_dir, is_file=False)
            save_scan_history(user_id, result, input_type="zip", files_to_save=files_to_save)

            logger.debug(f"Returning result for zip input: {json.dumps(result, indent=2)[:500]}...")
            return jsonify(result)
        except zipfile.BadZipFile:
            return jsonify({
                "results": {
                    "status": "error",
                    "message": "Le fichier ZIP est invalide",
                    "passed_checks": [],
                    "failed_checks": [],
                    "summary": {"passed": 0, "failed": 0}
                }
            }), 400
        except UnicodeDecodeError as e:
            logger.error(f"Failed to decode file in ZIP: {str(e)}")
            return jsonify({
                "results": {
                    "status": "error",
                    "message": "Erreur de décodage du fichier dans l’archive",
                    "passed_checks": [],
                    "failed_checks": [],
                    "summary": {"passed": 0, "failed": 0}
                }
            }), 400
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    elif input_type == "repo":
        repo_url = request.form.get("repo_url") or (request.json and request.json.get("repo_url"))
        if not repo_url:
            return jsonify({"error": "repo_url est requis"}), 400

        temp_dir = tempfile.mkdtemp()
        try:
            logger.debug(f"Cloning repository {repo_url} to {temp_dir}")
            clone_cmd = ["git", "clone", "--depth", "1", repo_url, temp_dir]
            subprocess.run(clone_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            git_dir = os.path.join(temp_dir, ".git")
            if os.path.exists(git_dir):
                def remove_readonly(func, path, _):
                    os.chmod(path, stat.S_IWRITE)
                    func(path)
                shutil.rmtree(git_dir, onerror=remove_readonly)

            if not any(f.endswith(('.tf', '.yaml', '.yml')) or f == "Dockerfile" for _, _, files in os.walk(temp_dir) for f in files):
                return jsonify({
                    "results": {
                        "status": "error",
                        "message": "Aucun fichier scannable trouvé dans le dépôt",
                        "passed_checks": [],
                        "failed_checks": [],
                        "summary": {"passed": 0, "failed": 0}
                    }
                }), 400

            result = run_checkov_on_dir(temp_dir, is_file=False)
            save_scan_history(user_id, result, input_type="repo", repo_url=repo_url)

            logger.debug(f"Returning result for repo input: {json.dumps(result, indent=2)[:1000]}...")
            return jsonify(result)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clone repository: {e.stderr}")
            return jsonify({"error": "Échec du clonage du dépôt GitHub", "details": e.stderr}), 400
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    return jsonify({"error": "Type d'entrée invalide. Utilisez 'file', 'zip', 'repo' ou 'content'"}), 400