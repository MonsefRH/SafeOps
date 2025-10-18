from unittest.mock import Mock, patch, mock_open
import pytest
@pytest.fixture
def checkov_mock_subprocess():
    mock_process = Mock()
    mock_process.stdout = '{"results": {"passed_checks": [], "failed_checks": []}}'
    mock_process.returncode = 0
    with patch("subprocess.run", return_value=mock_process) as mock_run:
        yield mock_run

@pytest.fixture
def checkov_mock_genai():
    mock_model = Mock()
    mock_response = Mock()
    mock_response.text = "Update resource to include encryption"
    mock_model.generate_content.return_value = mock_response
    with patch("services.checkov_service.genai.GenerativeModel", return_value=mock_model):
        yield mock_model

@pytest.fixture
def checkov_mock_db_session():
    mock_session = Mock()
    mock_session.add.return_value = None
    mock_session.commit.return_value = None
    mock_session.rollback.return_value = None
    mock_session.get.return_value = Mock(email="test@example.com", name="Test User")
    with patch("services.checkov_service.db.session", mock_session):
        yield mock_session

@pytest.fixture
def checkov_mock_selected_repo():
    mock_repo = Mock(id=1, full_name="user/repo", html_url="https://github.com/user/repo")
    with patch("services.checkov_service.SelectedRepo") as mock_class:
        mock_class.query.filter_by.return_value.first.return_value = mock_repo
        mock_class.return_value = mock_repo
        yield mock_class

@pytest.fixture
def checkov_mock_scan_history():
    mock_instance = Mock(id=1)
    with patch("services.checkov_service.ScanHistory") as mock_class:
        mock_class.return_value = mock_instance
        yield mock_class

@pytest.fixture
def checkov_mock_file_content():
    mock_instance = Mock()
    with patch("services.checkov_service.FileContent") as mock_class:
        mock_class.return_value = mock_instance
        yield mock_class

@pytest.fixture
def checkov_mock_file_system():
    with patch("os.path.exists", return_value=True), \
         patch("os.walk", return_value=[("/tmp", [], ["main.tf"])]), \
         patch("tempfile.mkdtemp", return_value="/tmp/test"), \
         patch("shutil.rmtree") as mock_rmtree, \
         patch("builtins.open", new_callable=mock_open(), read_data="resource aws_s3_bucket {}"):
        yield

@pytest.fixture
def checkov_mock_git_clone():
    mock_process = Mock(returncode=0, stdout="", stderr="")
    with patch("services.checkov_service.subprocess.run", return_value=mock_process) as mock_run:
        yield mock_run

@pytest.fixture
def checkov_mock_report_service():
    with patch("services.checkov_service.generate_csv_for_scan", return_value=("/tmp/report.csv", "report.csv")) as mock_csv, \
         patch("services.checkov_service.send_csv_report_email") as mock_email:
        yield {"csv": mock_csv, "email": mock_email}