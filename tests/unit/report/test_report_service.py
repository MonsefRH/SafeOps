import pytest
import os
from unittest.mock import Mock
from datetime import datetime, timezone
from services.report_service import generate_csv_for_scan, send_csv_report_email




def test_generate_csv_for_scan_checkov(
    report_mock_db_session,
    report_mock_scan_history,
    report_mock_user,
    report_mock_tempfile,
    report_mock_open_csv
):
    file_path, filename = generate_csv_for_scan(42)

    # Check filename structure (handle Windows backslashes)
    assert "safeops_report_checkov" in file_path
    assert "repo.git_42" in filename
    assert filename.endswith(".csv")
    assert os.path.basename(file_path) == filename

    # CSV content
    csv_content = "".join(report_mock_open_csv)
    assert "user_name,scan_type,repo,executed_at" in csv_content
    assert "Alice" in csv_content
    assert "checkov" in csv_content
    assert "CKV_AWS_123" in csv_content
    assert "S3 bucket should not be public" in csv_content
    assert "FAILED" in csv_content
    assert "PASSED" in csv_content


def test_generate_csv_for_scan_scan_not_found(report_mock_db_session):
    report_mock_db_session.get.return_value = None
    with pytest.raises(ValueError, match="scan_id not found"):
        generate_csv_for_scan(999)


def test_generate_csv_for_scan_semgrep(
    report_mock_db_session,
    report_mock_tempfile,
    report_mock_open_csv
):
    # Reset the mock to return modified scan
    modified_scan = Mock()
    modified_scan.id = 42
    modified_scan.user_id = 1
    modified_scan.scan_type = "semgrep"
    modified_scan.repo_url = "https://github.com/user/repo.git"
    modified_scan.status = "SUCCESS"
    modified_scan.created_at = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)
    modified_scan.scan_result = {
        "results": {
            "failed_checks": [
                {
                    "check_id": "python-lang-security",
                    "severity": "HIGH",
                    "message": "Use of hardcoded credentials",
                    "file_path": "/app/main.py",
                    "file_line_range": [5, 7],
                    "suggestion": "Use env vars"
                }
            ]
        },
        "meta": {"executed_at": "2025-01-01T12:00:00"}
    }

    mock_user = Mock()
    mock_user.id = 1
    mock_user.name = "Alice"

    report_mock_db_session.get.side_effect = lambda model, sid: (
        modified_scan if model.__name__ == "ScanHistory" else mock_user
    )

    generate_csv_for_scan(42)
    csv = "".join(report_mock_open_csv)
    assert "semgrep" in csv
    assert "python-lang-security" in csv
    assert "Use of hardcoded credentials" in csv


def test_generate_csv_for_scan_t5(
    report_mock_db_session,
    report_mock_tempfile,
    report_mock_open_csv
):
    # Modify the scan for t5
    modified_scan = Mock()
    modified_scan.id = 42
    modified_scan.user_id = 1
    modified_scan.scan_type = "t5"
    modified_scan.repo_url = "https://github.com/user/repo.git"
    modified_scan.status = "success"
    modified_scan.created_at = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)
    modified_scan.scan_result = {
        "explanation": "Fixed FROM ubuntu to FROM alpine",
        "meta": {"executed_at": "2025-01-01T12:00:00"}
    }

    mock_user = Mock()
    mock_user.id = 1
    mock_user.name = "Alice"

    report_mock_db_session.get.side_effect = lambda model, sid: (
        modified_scan if model.__name__ == "ScanHistory" else mock_user
    )

    generate_csv_for_scan(42)
    csv = "".join(report_mock_open_csv)
    assert "t5" in csv
    assert "T5_CORRECTION" in csv
    assert "Fixed FROM ubuntu to FROM alpine" in csv


def test_generate_csv_for_scan_unknown_type(
    report_mock_db_session,
    report_mock_tempfile,
    report_mock_open_csv
):
    # Modify the scan for unknown type
    modified_scan = Mock()
    modified_scan.id = 42
    modified_scan.user_id = 1
    modified_scan.scan_type = "unknown"
    modified_scan.repo_url = "https://github.com/user/repo.git"
    modified_scan.status = "success"
    modified_scan.created_at = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)
    modified_scan.scan_result = {"meta": {"executed_at": "2025-01-01T12:00:00"}}

    mock_user = Mock()
    mock_user.id = 1
    mock_user.name = "Alice"

    report_mock_db_session.get.side_effect = lambda model, sid: (
        modified_scan if model.__name__ == "ScanHistory" else mock_user
    )

    generate_csv_for_scan(42)
    csv = "".join(report_mock_open_csv)
    assert "unknown" in csv
    assert "No parser for this scan_type" in csv


def test_send_csv_report_email(
    report_mock_smtp,
    report_mock_open_csv
):
    csv_path = "/tmp/fake_report.csv"
    csv_filename = "report.csv"

    send_csv_report_email(
        to_email="user@example.com",
        subject="Your Report",
        body_text="Here is your scan report.\nSee attached.",
        csv_path=csv_path,
        csv_filename=csv_filename,
        user_name="Bob"
    )

    # Verify SMTP was called
    smtp = report_mock_smtp.return_value.__enter__.return_value
    smtp.login.assert_called_once()
    smtp.send_message.assert_called_once()

    # Get the message
    msg = smtp.send_message.call_args[0][0]

    # Verify headers
    assert msg["To"] == "user@example.com"
    assert msg["Subject"] == "Your Report"
    assert msg["From"] is not None

    # Verify the message content contains user name
    # Convert message to string to check content
    msg_str = str(msg)
    assert "Bob" in msg_str
    assert "SafeOps" in msg_str