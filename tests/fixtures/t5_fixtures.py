import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_tokenizer():
    """Mock tokenizer to return a proper BatchEncoding-like dict."""
    mock_tok = Mock()

    mock_input_ids = Mock()  # Simulates torch.tensor
    mock_input_ids.to = Mock(return_value=mock_input_ids)  # .to(device) returns self

    mock_attention_mask = Mock()
    mock_attention_mask.to = Mock(return_value=mock_attention_mask)

    # Create mock BatchEncoding: Mock with dict behavior + .to
    mock_batch = Mock()
    mock_batch.to = Mock(return_value=mock_batch)  # .to(device) returns self
    mock_batch.keys.return_value = ['input_ids', 'attention_mask']
    mock_batch.__getitem__ = lambda self, key: {
        'input_ids': mock_input_ids,
        'attention_mask': mock_attention_mask
    }[key]

    # Mock the tokenizer call
    mock_tok.return_value = mock_batch

    # Mock decode for outputs[0]
    mock_tok.decode.return_value = "fixed Dockerfile content"

    with patch("services.t5_service.tokenizer", mock_tok):
        yield mock_tok

@pytest.fixture
def mock_t5_model():
    """Mock T5 model."""
    mock_model = Mock()
    mock_model.device = "cpu"

    mock_output_tensor = Mock()  # Simulates generated token IDs tensor
    mock_outputs = [mock_output_tensor]  # List for batch (outputs[0])
    mock_model.generate.return_value = mock_outputs

    with patch("services.t5_service.t5_model", mock_model):
        yield mock_model

@pytest.fixture
def mock_genai():
    mock_model = Mock()
    mock_response = Mock()
    mock_response.text = "Line 1: Fixed security issue..."
    mock_model.generate_content.return_value = mock_response
    with patch("services.t5_service.genai.GenerativeModel", return_value=mock_model):
        yield mock_model

@pytest.fixture
def mock_scan_history():
    """Mock ScanHistory class to avoid mapper configuration errors."""
    mock_instance = Mock(id=1)  # Mock instance with .id
    with patch("services.t5_service.ScanHistory") as mock_class:
        mock_class.return_value = mock_instance
        yield mock_class



@pytest.fixture
def t5_mock_db_session(mock_scan_history):
    """Mock db.session (includes ScanHistory mock)."""
    mock_session = Mock()
    mock_session.add.return_value = None
    mock_session.commit.return_value = None
    mock_session.rollback.return_value = None
    mock_session.flush.return_value = Mock(id=1)  # For .id access

    with patch("services.t5_service.db.session", mock_session):
        yield mock_session

