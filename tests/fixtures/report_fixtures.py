import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone


@pytest.fixture
def report_mock_scan_history():
    scan = Mock()
    scan.id = 42
    scan.user_id = 1
    scan.scan_type = "checkov"
    scan.repo_url = "https://github.com/user/repo.git"
    scan.status = "SUCCESS"
    scan.created_at = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)
    scan.scan_result = {
        "failed_checks": [
            {
                "check_id": "CKV_AWS_123",
                "check_name": "S3 bucket should not be public",
                "severity": "HIGH",
                "file_path": "/infra/s3.tf",
                "file_line_range": [10, 15],
                "resource": "aws_s3_bucket.public",
                "suggestion": "Set `acl = private`"
            }
        ],
        "passed_checks": [
            {
                "check_id": "CKV_AWS_999",
                "check_name": "EC2 has tags",
                "file_path": "/infra/ec2.tf",
                "file_line_range": [20, 25],
                "resource": "aws_instance.web"
            }
        ],
        "path_scanned": "/infra",
        "meta": {"executed_at": "2025-01-01T12:00:00"}
    }
    return scan


@pytest.fixture
def report_mock_user():
    user = Mock()
    user.id = 1
    user.name = "Alice"
    return user


@pytest.fixture
def report_mock_db_session(report_mock_scan_history, report_mock_user):
    sess = Mock()
    sess.get.side_effect = lambda model, sid: (
        report_mock_scan_history if model.__name__ == "ScanHistory" and sid == 42 else
        report_mock_user if model.__name__ == "User" and sid == 1 else
        None
    )
    sess.add.return_value = None
    sess.commit.return_value = None

    with patch("services.report_service.db.session", sess):
        yield sess


@pytest.fixture
def report_mock_smtp():
    with patch("services.report_service.smtplib.SMTP_SSL") as mock:
        smtp = Mock()
        mock.return_value.__enter__.return_value = smtp
        smtp.login.return_value = None
        smtp.send_message.return_value = None
        yield mock


@pytest.fixture
def report_mock_tempfile():
    with patch("services.report_service.tempfile.gettempdir", return_value="/tmp"):
        yield


@pytest.fixture
def report_mock_open_csv():
    """Mock open() for CSV and file operations - captures written content."""
    written_lines = []

    def side_effect_open(file_path, mode="r", **kwargs):
        mock_file = MagicMock()

        if "w" in mode:
            # Write mode - capture content
            def write_mock(content):
                written_lines.append(content)
                return len(content)

            mock_file.write = write_mock
            mock_file.__enter__ = Mock(return_value=mock_file)
            mock_file.__exit__ = Mock(return_value=False)

        elif "b" in mode:
            # Binary read mode (for email attachment)
            mock_file.read.return_value = b"test,csv,content\n1,2,3"
            mock_file.__enter__ = Mock(return_value=mock_file)
            mock_file.__exit__ = Mock(return_value=False)
        else:
            # Text read mode
            mock_file.read.return_value = "test,csv,content\n1,2,3"
            mock_file.__enter__ = Mock(return_value=mock_file)
            mock_file.__exit__ = Mock(return_value=False)

        return mock_file

    with patch("builtins.open", side_effect=side_effect_open):
        yield written_lines