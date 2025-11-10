import pytest
from unittest.mock import Mock, patch, mock_open


@pytest.fixture
def fullscan_mock_repo():
    with patch("services.full_scan_service.Repo.clone_from") as mock:
        yield mock

@pytest.fixture
def fullscan_mock_tempdir():
    with patch("services.full_scan_service.tempfile.TemporaryDirectory") as mock:
        mock.return_value.__enter__.return_value = "/tmp/repo"
        yield mock

@pytest.fixture
def fullscan_mock_os_walk():
    with patch("services.full_scan_service.os.walk") as mock:
        mock.return_value = [("/tmp/repo", [], ["Dockerfile", "main.tf", "app.yml"])]
        yield mock
@pytest.fixture
def fullscan_mock_open():
    m = mock_open()
    m.return_value.__enter__.return_value.read.side_effect = [
        "FROM alpine\n",
        "resource aws_s3 {}\n",
        "apiVersion: v1\n"
    ]
    with patch("services.full_scan_service.open", m):
        yield m

@pytest.fixture
def fullscan_mock_requests():
    corrections = [
        {"correction": "FROM alpine:latest\n"},
        {"correction": "resource aws_s3_bucket {}\n"},
        {"correction": "apiVersion: v1\nkind: Pod\n"}
    ]
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.side_effect = corrections
    with patch("services.full_scan_service.requests.post", return_value=mock_resp) as mock:
        yield mock
@pytest.fixture
def fullscan_mock_checkov():
    mock_result = {"meta": {}, "results": {"summary": {"failed": 0}}}
    with patch("services.full_scan_service.run_checkov_on_dir", return_value=mock_result) as mock_run, \
         patch("services.full_scan_service.save_checkov_history", return_value=42) as mock_save:
        yield {"run": mock_run, "save": mock_save, "result": mock_result}

@pytest.fixture
def fullscan_mock_semgrep():
    mock_result = {"scan_id": 7, "status": "success"}
    with patch("services.full_scan_service.run_semgrep", return_value=mock_result) as mock:
        yield mock

@pytest.fixture
def fullscan_mock_datetime():
    mock_dt = Mock()
    mock_dt.utcnow.return_value.isoformat.return_value = "2025-11-02T12:00:00"
    with patch("services.full_scan_service.datetime", mock_dt):
        yield mock_dt

