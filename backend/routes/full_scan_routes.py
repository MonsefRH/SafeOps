import os
import tempfile
import logging
import requests

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from git import Repo

from routes.checkov import run_checkov_on_dir
from routes.semgrep import run_semgrep_scan

full_scan_bp = Blueprint("full_scan", __name__)
logger = logging.getLogger(__name__)

SUPPORTED_CONFIG_FILES = ["Dockerfile", ".tf", ".yml", ".yaml"]

def collect_config_files(root_dir):
    matched_files = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if (
                file == "Dockerfile"
                or file.endswith(".tf")
                or file.endswith(".yml")
                or file.endswith(".yaml")
            ):
                matched_files.append(os.path.join(root, file))
    return matched_files

def call_t5_fix(file_path, jwt_token):
    try:
        with open(file_path, "r") as f:
            content = f.read()

        if not content.strip():
            return None, "Empty file"

        response = requests.post(
            "http://localhost:5000/t5",
            headers={"Authorization": jwt_token},
            json={"dockerfile": content}  # even for tf/yml we reuse the same key
        )

        if response.status_code == 200:
            data = response.json()
            return data.get("correction", ""), None
        else:
            return None, f"T5 error {response.status_code}: {response.text}"
    except Exception as e:
        return None, f"Exception during T5 fix: {e}"

@full_scan_bp.route("/full-scan", methods=["POST"])
@jwt_required()
def full_scan():
    try:
        data = request.get_json()
        repo_url = data.get("repo_url")
        if not repo_url:
            return jsonify({"error": "Missing repo_url"}), 400

        user_id = get_jwt_identity()
        jwt_token = request.headers.get("Authorization")

        with tempfile.TemporaryDirectory() as tmpdirname:
            logger.debug(f"Cloning {repo_url} into {tmpdirname}")
            Repo.clone_from(repo_url, tmpdirname)

            results = {
                "checkov": {},
                "t5": {},
                "checkov_corrected": {},
                "semgrep": {}
            }

            # === Step 1: Initial Checkov ===
            try:
                checkov_result = run_checkov_on_dir(tmpdirname, is_file=False)
                results["checkov"] = checkov_result
            except Exception as e:
                logger.error(f"Checkov scan failed: {e}")
                results["checkov"] = {"error": str(e)}

            # === Step 2: T5 Correction on Supported Files ===
            t5_summary = {}
            config_files = collect_config_files(tmpdirname)

            for filepath in config_files:
                rel_path = os.path.relpath(filepath, tmpdirname)
                correction, error = call_t5_fix(filepath, jwt_token)
                if correction:
                    with open(filepath, "w") as f:
                        f.write(correction)
                    t5_summary[rel_path] = {"corrected": True}
                else:
                    t5_summary[rel_path] = {"corrected": False, "error": error}

            results["t5"] = t5_summary

            # === Step 3: Re-run Checkov after correction ===
            try:
                corrected_checkov_result = run_checkov_on_dir(tmpdirname, is_file=False)
                results["checkov_corrected"] = corrected_checkov_result
            except Exception as e:
                logger.error(f"Corrected Checkov scan failed: {e}")
                results["checkov_corrected"] = {"error": str(e)}

            # === Step 4: Semgrep ===
            try:
                semgrep_result = run_semgrep_scan(tmpdirname, user_id=user_id, repo_url=repo_url)
                results["semgrep"] = semgrep_result
            except Exception as e:
                logger.error(f"Semgrep scan failed: {e}")
                results["semgrep"] = {"error": str(e)}

            return jsonify(results)

    except Exception as e:
        logger.exception("Full scan failed")
        return jsonify({"error": str(e)}), 500
