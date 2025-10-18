import pytest
from unittest.mock import Mock, patch


@pytest.fixture
def semgrep_mock_subprocess():
    mock_process = Mock()
    mock_process.stdout = '{"results": []}'
    mock_process.returncode = 0
    with patch("services.semgrep_service.subprocess.run", return_value=mock_process) as mock_run:
        yield mock_run

@pytest.fixture
def semgrep_mock_genai():
    mock_model = Mock()
    mock_response = Mock()
    mock_response.text = "Use secure function instead"
    mock_model.generate_content.return_value = mock_response
    with patch("services.semgrep_service.genai.GenerativeModel", return_value=mock_model):
        yield mock_model

@pytest.fixture
def semgrep_mock_db_session():
    mock_session = Mock()
    mock_session.add.return_value = None
    mock_session.commit.return_value = None
    mock_session.rollback.return_value = None
    mock_session.get.return_value = Mock(email="test@example.com", name="Test User")
    with patch("services.semgrep_service.db.session", mock_session):
        yield mock_session

@pytest.fixture
def semgrep_mock_scan_history():
    mock_instance = Mock(id=1)
    with patch("services.semgrep_service.ScanHistory") as mock_class:
        mock_class.return_value = mock_instance
        yield mock_class

@pytest.fixture
def semgrep_mock_git_repo():
    mock_repo = Mock()
    with patch("services.semgrep_service.Repo.clone_from", return_value=mock_repo) as mock_clone:
        yield mock_clone

@pytest.fixture
def semgrep_mock_file_system():
    with patch("os.path.exists", return_value=True), \
         patch("os.path.join", side_effect=lambda *args: "/".join(args)), \
         patch("tempfile.mkdtemp", return_value="/tmp/test"), \
         patch("shutil.rmtree") as mock_rmtree, \
         patch("builtins.open", new_callable=pytest.mock_open, read_data="print(secret)"):
        yield

@pytest.fixture
def semgrep_mock_file():
    mock_file = Mock()
    mock_file.filename = "test.py"
    mock_file.save = Mock()
    return mock_file

@pytest.fixture
def semgrep_mock_report_service():
    with patch("services.semgrep_service.generate_csv_for_scan", return_value=("/tmp/report.csv", "report.csv")) as mock_csv, \
         patch("services.semgrep_service.send_csv_report_email") as mock_email:
        yield {"csv": mock_csv, "email": mock_email}