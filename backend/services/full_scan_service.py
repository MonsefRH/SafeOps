import os
import tempfile
import logging
import requests
from datetime import datetime
from git import Repo

from services.checkov_service import run_checkov_on_dir, save_scan_history as save_checkov_history
from services.semgrep_service import run_semgrep

# Reuse logger from checkov
logger = logging.getLogger(__name__)

SUPPORTED_CONFIG_FILES = ["Dockerfile", ".tf", ".yml", ".yaml"]


def collect_config_files(root_dir):
    """Collect supported configuration files from a directory."""
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
    """Call the T5 correction API for a file."""
    try:
        with open(file_path, "r") as f:
            content = f.read()

        if not content.strip():
            return None, "Empty file"

        response = requests.post(
            "http://localhost:5000/t5",
            headers={"Authorization": jwt_token},
            json={"dockerfile": content}  # Reusing 'dockerfile' key for all file types
        )

        if response.status_code == 200:
            data = response.json()
            return data.get("correction", ""), None
        else:
            return None, f"T5 error {response.status_code}: {response.text}"
    except Exception as e:
        return None, f"Exception during T5 fix: {str(e)}"


def _repo_full_name_from_url(repo_url: str) -> str:
    try:
        parts = repo_url.rstrip("/").split("/")
        return f"{parts[-2]}/{parts[-1]}" if len(parts) >= 2 else parts[-1]
    except Exception:
        return repo_url


def run_full_scan(user_id, repo_url, jwt_token):
    """
    Run a full scan (Checkov initial, T5 correction, Checkov re-run, Semgrep) on a repository.
    - Les notifications + envoi de CSV sont gérés dans les services concernés (Checkov/Semgrep).
    - Ici on ajoute seulement meta.executed_at aux résultats Checkov avant la sauvegarde.
    """
    try:
        with tempfile.TemporaryDirectory() as tmpdirname:
            logger.debug(f"Cloning {repo_url} into {tmpdirname}")
            Repo.clone_from(repo_url, tmpdirname)

            results = {
                "checkov": {},
                "t5": {},
                "checkov_corrected": {},
                "semgrep": {}
            }

            repo_full_name = _repo_full_name_from_url(repo_url)

            # Step 1: Initial Checkov scan
            try:
                checkov_result = run_checkov_on_dir(tmpdirname, is_file=False)
                # ➕ horodatage d'exécution
                checkov_result.setdefault("meta", {})
                checkov_result["meta"]["executed_at"] = datetime.utcnow().isoformat() + "Z"

                scan_id = save_checkov_history(
                    user_id=user_id,
                    result=checkov_result,
                    input_type="repo",
                    repo_url=repo_url
                )
                results["checkov"] = {"scan_id": scan_id, "results": checkov_result}
            except Exception as e:
                logger.error(f"Checkov scan failed: {str(e)}")
                results["checkov"] = {"error": str(e)}

            # Step 2: T5 Correction on Supported Files (appel de l'API /t5)
            t5_summary = {}
            config_files = collect_config_files(tmpdirname)

            for filepath in config_files:
                rel_path = os.path.relpath(filepath, tmpdirname)
                correction, error = call_t5_fix(filepath, jwt_token)
                if correction:
                    with open(filepath, "w") as f:
                        f.write(correction)
                    t5_summary[rel_path] = {
                        "corrected": True,
                        "content": correction
                    }
                else:
                    t5_summary[rel_path] = {"corrected": False, "error": error}
            results["t5"] = t5_summary

            # Step 3: Re-run Checkov after correction
            try:
                corrected_checkov_result = run_checkov_on_dir(tmpdirname, is_file=False)
                corrected_checkov_result.setdefault("meta", {})
                corrected_checkov_result["meta"]["executed_at"] = datetime.utcnow().isoformat() + "Z"

                scan_id = save_checkov_history(
                    user_id=user_id,
                    result=corrected_checkov_result,
                    input_type="repo",
                    repo_url=repo_url
                )
                results["checkov_corrected"] = {"scan_id": scan_id, "results": corrected_checkov_result}
            except Exception as e:
                logger.error(f"Corrected Checkov scan failed: {str(e)}")
                results["checkov_corrected"] = {"error": str(e)}

            # Step 4: Semgrep scan
            try:
                semgrep_result = run_semgrep(
                    user_id=user_id,
                    input_type="repo",
                    repo_url=repo_url,
                    file_path=tmpdirname
                )
                results["semgrep"] = semgrep_result
            except Exception as e:
                logger.error(f"Semgrep scan failed: {str(e)}")
                results["semgrep"] = {"error": str(e)}

            return results
    except Exception as e:
        logger.exception("Full scan failed")
        raise RuntimeError(f"Full scan failed: {str(e)}")
