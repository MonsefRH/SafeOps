import subprocess
import tempfile
import json
from git import Repo
from utils.db import db
from models.scan_history import ScanHistory
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s:%(name)s: %(message)s',
    handlers=[logging.FileHandler('scan_app.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def run_scan(user_id, repo_url):
    """Clone a repository and run a Semgrep scan."""
    if not repo_url:
        logger.error("Missing repo_url for scan")
        raise ValueError("Le champ 'repo_url' est requis")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.debug(f"Cloning {repo_url} into {temp_dir}")
            Repo.clone_from(repo_url, temp_dir)

            semgrep_result = subprocess.run(
                ['semgrep', 'scan', temp_dir, '--config=auto', '--json'],
                capture_output=True, text=True, check=True
            )

            result_json = json.loads(semgrep_result.stdout)
            findings = result_json.get("results", [])
            exit_code = 1 if findings else 0
            status = "failed" if findings else "success"

            # Save scan result to database
            scan_history = ScanHistory(
                user_id=user_id,
                scan_type="semgrep",
                input_type="repo",
                repo_url=repo_url,
                scan_result={
                    "status": status,
                    "exit_code": exit_code,
                    "findings": findings
                },
                status=status,
                score=100 if exit_code == 0 else 50,  # Example scoring
                compliant=exit_code == 0
            )
            db.session.add(scan_history)
            db.session.commit()

            logger.info(f"Semgrep scan completed for user_id {user_id}, repo_url {repo_url}: {status}")
            return {
                "scan_id": scan_history.id,
                "status": status,
                "exit_code": exit_code,
                "findings": findings
            }

    except subprocess.CalledProcessError as e:
        logger.error(f"Semgrep execution error for repo_url {repo_url}: {str(e)}")
        raise RuntimeError("Semgrep execution error")
    except Exception as e:
        logger.error(f"Failed to scan repo_url {repo_url}: {str(e)}")
        db.session.rollback()
        raise RuntimeError(str(e))