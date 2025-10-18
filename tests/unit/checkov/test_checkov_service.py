import subprocess
from unittest.mock import patch

import pytest
from services.checkov_service import run_checkov_scan, run_checkov_on_single_file, run_checkov_on_dir, save_scan_history

def test_run_checkov_scan_content_valid(
    checkov_mock_subprocess, checkov_mock_genai, checkov_mock_db_session,
    checkov_mock_selected_repo, checkov_mock_scan_history, checkov_mock_file_content,
    checkov_mock_file_system, checkov_mock_report_service
):
    result = run_checkov_scan(
        user_id=1, input_type="content", content="resource aws_s3_bucket {}"
    )
    assert result["scan_id"] == 1
    assert result["results"]["status"] == "success"
    assert result["results"]["path_scanned"].endswith("input.tf")
    assert result["results"]["files_found"] == ["test/input.tf"]
    assert checkov_mock_db_session.add.call_count >= 2  # ScanHistory + FileContent
    assert checkov_mock_db_session.commit.called
    assert checkov_mock_report_service["email"].called

def test_run_checkov_scan_content_empty(
    checkov_mock_subprocess, checkov_mock_genai, checkov_mock_db_session,
    checkov_mock_selected_repo, checkov_mock_scan_history, checkov_mock_file_content
):
    with pytest.raises(ValueError, match="Content is required"):
        run_checkov_scan(user_id=1, input_type="content", content="")

def test_run_checkov_scan_file_missing(
    checkov_mock_subprocess, checkov_mock_genai, checkov_mock_db_session,
    checkov_mock_selected_repo, checkov_mock_scan_history, checkov_mock_file_content,
    checkov_mock_file_system
):
    with patch("os.path.exists", return_value=False):
        with pytest.raises(ValueError, match="Le fichier /main.tf n'existe pas"):
            run_checkov_scan(user_id=1, input_type="file", file_path="/main.tf")

def test_run_checkov_scan_repo_valid(
    checkov_mock_subprocess, checkov_mock_genai, checkov_mock_db_session,
    checkov_mock_selected_repo, checkov_mock_scan_history, checkov_mock_file_content,
    checkov_mock_file_system, checkov_mock_git_clone, checkov_mock_report_service
):
    result = run_checkov_scan(
        user_id=1, input_type="repo", repo_url="https://github.com/user/repo"
    )
    assert result["scan_id"] == 1
    assert result["results"]["status"] == "completed"
    assert result["results"]["files_found"] == ["main.tf"]
    assert checkov_mock_git_clone
    assert checkov_mock_report_service["email"].called

def test_run_checkov_on_single_file_valid(
    checkov_mock_subprocess, checkov_mock_genai, checkov_mock_file_system
):
    result = run_checkov_on_single_file("/tmp/main.tf")
    assert result["status"] == "success"
    assert result["path_scanned"] == "main.tf"
    assert result["summary"] == {"passed": 0, "failed": 0}

def test_run_checkov_on_single_file_timeout(
    checkov_mock_subprocess, checkov_mock_genai, checkov_mock_file_system
):
    checkov_mock_subprocess.side_effect = subprocess.TimeoutExpired(cmd=["checkov"], timeout=60)
    result = run_checkov_on_single_file("/tmp/main.tf")
    assert result["status"] == "timeout"
    assert "timed out" in result["message"]

def test_run_checkov_on_dir_no_files(
    checkov_mock_subprocess, checkov_mock_genai, checkov_mock_file_system
):
    with patch("os.walk", return_value=[("/tmp", [], [])]):
        result = run_checkov_on_dir("/tmp")
        assert result["status"] == "error"
        assert "Aucun fichier scannable" in result["message"]

def test_save_scan_history_with_repo(
    checkov_mock_db_session, checkov_mock_selected_repo, checkov_mock_scan_history,
    checkov_mock_file_content, checkov_mock_report_service
):
    result = {
        "status": "success",
        "path_scanned": "/tmp",
        "files_found": ["main.tf"],
        "passed_checks": [],
        "failed_checks": [],
        "summary": {"passed": 0, "failed": 0},
        "score": 0,
        "compliant": False
    }
    scan_id = save_scan_history(
        user_id=1, result=result, input_type="repo",
        repo_url="https://github.com/user/repo", files_to_save=[("main.tf", "content")]
    )
    assert scan_id == 1
    assert checkov_mock_db_session.add.call_count >= 2  # SelectedRepo + ScanHistory
    assert checkov_mock_db_session.commit.called
    assert checkov_mock_report_service["email"].called