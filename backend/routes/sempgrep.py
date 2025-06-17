from flask import Blueprint, request, jsonify
import os
import tempfile
import zipfile
import requests
import json
import logging
import shutil
from pathlib import Path
from psycopg2.extras import Json
from utils.db import get_db_connection

semgrep_bp = Blueprint('semgrep', __name__)

# Configure upload folder
UPLOAD_FOLDER = "Uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s:%(name)s: %(message)s',
    handlers=[
        logging.FileHandler('semgrep_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def clean_path(full_path):
    """Remove temporary directory prefix from file paths."""
    try:
        path = Path(full_path)
        temp_dir = None
        for part in path.parts:
            if part.startswith('tmp') and len(part) > 3:  # e.g., tmpfxvp96iv
                temp_dir = part
                break
        if temp_dir:
            temp_index = path.parts.index(temp_dir)
            relative_path = '/'.join(path.parts[temp_index + 1:])
            return relative_path if relative_path else os.path.basename(full_path)
        logger.warning(f"No temporary directory found in path: {full_path}")
        return str(path)
    except Exception as e:
        logger.error(f"Error cleaning path {full_path}: {str(e)}")
        return str(full_path)


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
                (scan_id, clean_path(file_path), content, input_type)
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
        print(repo_url)
        # Normalize paths in files_found
        if result.get("results", {}).get("files_found"):
            result["results"]["files_found"] = [clean_path(f) for f in result["results"]["files_found"]]

        # Calculate score and compliant fields
        total_passed = result.get("results", {}).get("summary", {}).get("passed", 0)
        total_failed = result.get("results", {}).get("summary", {}).get("failed", 0)
        total_checks = total_passed + total_failed
        score = round((total_passed / total_checks) * 100) if total_checks > 0 else 0
        compliant = score == 100
        result["results"]["score"] = score
        result["results"]["compliant"] = compliant

        # Set path_scanned if missing
        if not result.get("results", {}).get("path_scanned"):
            result["results"]["path_scanned"] = clean_path(tempfile.gettempdir())

        # Insert scan history
        cursor.execute(
            """
            INSERT INTO scan_history (user_id, scan_result, repo_url, status, score, compliant, input_type , scan_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s , %s)
            RETURNING id
            """,
            (
                user_id,
                Json(result),
                repo_url,
                result.get("status", "unknown"),
                score,
                compliant,
                input_type,
                'semgrep'  # Set scan_type to semgrep
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


@semgrep_bp.route("/semgrep", methods=["POST"])
def validate():
    input_type = request.form.get("input_type")
    user_id = request.headers.get("X-User-ID") or (request.json and request.json.get("user_id"))
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    SEMGREP_ENDPOINT = "http://" +os.getenv("MACHINE_IP")+":5000/scan"

    if input_type == "file":
        content = request.form.get("content")
        extension = request.form.get("extension", "py")  # Default to .py

        if content:
            # Handle raw code content
            if not content.strip():
                return jsonify({"error": "Content cannot be empty"}), 400

            # Prepare form data for Semgrep endpoint
            form_data = {
                "input_type": "file",
                "content": content,
                "extension": extension
            }

            # Send as multipart/form-data
            response = requests.post(
                SEMGREP_ENDPOINT,
                data=form_data
            )

            if response.status_code != 200:
                error_data = response.json()
                raise Exception(error_data.get("error", "Failed to scan content"))

            result = response.json()
            # Store content with appropriate file extension
            files_to_save = [(f"input.{extension}", content)]
            save_scan_history(user_id, result, input_type="content", files_to_save=files_to_save)

            logger.debug(f"Returning result for content input: {json.dumps(result, indent=2)[:500]}...")
            return jsonify(result)

        elif "file" in request.files:
            # Handle file upload
            file = request.files["file"]
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            try:
                file.save(file_path)
                with open(file_path, "r", encoding="utf-8") as f:
                    file_content = f.read()

                # Prepare form data: separate fields and file
                data = {
                    "input_type": "file" if not file.filename.endswith(".zip") else "zip"
                }
                files = {
                    "file": (file.filename, open(file_path, "rb"), "application/octet-stream")
                }
                response = requests.post(SEMGREP_ENDPOINT, data=data, files=files)

                # Close the file after the request
                files["file"][1].close()

                if response.status_code != 200:
                    error_data = response.json()
                    raise Exception(error_data.get("error", "Failed to scan file"))

                result = response.json()
                files_to_save = [(file.filename, file_content)]
                save_scan_history(user_id, result, input_type="file", files_to_save=files_to_save)

                logger.debug(f"Returning result for file input: {json.dumps(result, indent=2)[:500]}...")
                return jsonify(result)
            finally:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except PermissionError as e:
                    logger.warning(f"Could not delete {file_path}: {str(e)}. File may still be in use.")
                except Exception as e:
                    logger.error(f"Failed to delete {file_path}: {str(e)}")

        else:
            return jsonify({"error": "No file or content provided"}), 400

    elif input_type == "zip" and "file" in request.files:
        file = request.files["file"]
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, file.filename)
        try:
            file.save(zip_path)
            extract_dir = os.path.join(temp_dir, "extracted")
            os.makedirs(extract_dir)
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)

            files_to_save = []
            for root, _, files in os.walk(extract_dir):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        files_to_save.append((file_path, content))
                    except UnicodeDecodeError:
                        logger.warning(f"Skipping non-text file {file_path}")
                        continue

            data = {"input_type": "zip"}
            files = {"file": (file.filename, open(zip_path, "rb"), "application/zip")}
            response = requests.post(SEMGREP_ENDPOINT, data=data, files=files)

            files["file"][1].close()

            if response.status_code != 200:
                error_data = response.json()
                raise Exception(error_data.get("error", "Failed to scan zip"))

            result = response.json()
            save_scan_history(user_id, result, input_type="zip", files_to_save=files_to_save)

            logger.debug(f"Returning result for zip input: {json.dumps(result, indent=2)[:500]}...")
            return jsonify(result)
        except zipfile.BadZipFile:
            return jsonify({"error": "Invalid ZIP file"}), 400
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    elif input_type == "repo":
        repo_url = request.form.get("repo_url")
        if not repo_url:
            return jsonify({"error": "repo_url is required"}), 400

        form_data = {
            "input_type": "repo",
            "repo_url": repo_url
        }
        response = requests.post(SEMGREP_ENDPOINT, data=form_data)

        if response.status_code != 200:
            error_data = response.json()
            raise Exception(error_data.get("error", "Failed to scan repository"))

        result = response.json()
        save_scan_history(user_id, result, input_type="repo", repo_url=repo_url)

        logger.debug(f"Returning result for repo input: {json.dumps(result, indent=2)[:500]}...")
        return jsonify(result)

    return jsonify({"error": "Invalid input type. Use 'file', 'zip', 'repo'"}), 400