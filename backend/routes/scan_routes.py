from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
import subprocess
import tempfile
import json

scan_bp = Blueprint("scan", __name__)

@scan_bp.route('/scan', methods=['POST'])
@jwt_required()
def scan_repo():
    try:
        data = request.get_json()
        repo_url = data.get('repo_url')

        if not repo_url:
            return jsonify({"status": "failed", "error": "Le champ 'repo_url' est requis"}), 400

        with tempfile.TemporaryDirectory() as temp_dir:
            subprocess.run(['git', 'clone', repo_url, temp_dir], check=True)
            semgrep_result = subprocess.run(
                ['semgrep', 'scan', temp_dir, '--config=auto', '--json'],
                capture_output=True, text=True
            )

            if semgrep_result.returncode >= 2:
                return jsonify({"status": "failed", "error": "Semgrep execution error"}), 500

            result_json = json.loads(semgrep_result.stdout)
            findings = result_json.get("results", [])
            exit_code = 1 if findings else 0
            status = "failed" if findings else "success"

            return jsonify({
                "status": status,
                "exit_code": exit_code,
                "findings": findings
            }), 200

    except Exception as e:
        print(f"Erreur serveur: {e}")
        return jsonify({"status": "failed", "error": str(e)}), 500