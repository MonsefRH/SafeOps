import pytest
from services.full_scan_service import run_full_scan

def test_run_full_scan_success(
    fullscan_mock_repo,
    fullscan_mock_tempdir,
    fullscan_mock_os_walk,
    fullscan_mock_open,
    fullscan_mock_requests,
    fullscan_mock_checkov,
    fullscan_mock_semgrep,
    fullscan_mock_datetime,

):
    result = run_full_scan(user_id=1, repo_url="https://github.com/u/r", jwt_token="jwt")

    assert "checkov" in result
    assert result["checkov"]["scan_id"] == 42
    assert result["checkov"]["results"]["meta"]["executed_at"] == "2025-11-02T12:00:00Z"

    assert len(result["t5"]) == 3
    assert result["t5"]["Dockerfile"]["corrected"] is True
    assert result["t5"]["Dockerfile"]["content"] == "FROM alpine:latest\n"

    assert result["t5"]["main.tf"]["corrected"] is True
    assert result["t5"]["main.tf"]["content"] == "resource aws_s3_bucket {}\n"

    assert result["t5"]["app.yml"]["corrected"] is True
    assert result["t5"]["app.yml"]["content"] == "apiVersion: v1\nkind: Pod\n"

    assert result["checkov_corrected"]["scan_id"] == 42
    assert result["checkov"]["results"]["meta"]["executed_at"] == "2025-11-02T12:00:00Z"

    assert result["semgrep"]["scan_id"] == 7

    fullscan_mock_checkov["save"].assert_called()
    fullscan_mock_repo.assert_called_once()
    assert fullscan_mock_requests.call_count == 3

def test_run_full_scan_checkov_fails(
    fullscan_mock_repo,
    fullscan_mock_tempdir,
    fullscan_mock_os_walk,
    fullscan_mock_open,
    fullscan_mock_requests,
    fullscan_mock_checkov,
    fullscan_mock_semgrep,
    fullscan_mock_datetime,
):
    fullscan_mock_checkov["run"].side_effect = Exception("checkov down")

    result = run_full_scan(user_id=1, repo_url="https://github.com/u/r", jwt_token="jwt")

    assert "error" in result["checkov"]
    assert "checkov down" in result["checkov"]["error"]

def test_run_full_scan_t5_api_fails(
    fullscan_mock_repo,
    fullscan_mock_tempdir,
    fullscan_mock_os_walk,
    fullscan_mock_open,
    fullscan_mock_requests,
    fullscan_mock_checkov,
    fullscan_mock_semgrep,
    fullscan_mock_datetime,
):
    fullscan_mock_requests.return_value.status_code = 500
    fullscan_mock_requests.return_value.text = "server error"

    result = run_full_scan(user_id=1, repo_url="https://github.com/u/r", jwt_token="jwt")

    assert result["t5"]["Dockerfile"]["corrected"] is False
    assert "T5 error 500" in result["t5"]["Dockerfile"]["error"]

def test_run_full_scan_clone_fails(
    fullscan_mock_repo,
    fullscan_mock_tempdir,

):
    fullscan_mock_repo.side_effect = Exception("git error")

    with pytest.raises(RuntimeError, match="Full scan failed"):
        run_full_scan(user_id=1, repo_url="invalid", jwt_token="jwt")

