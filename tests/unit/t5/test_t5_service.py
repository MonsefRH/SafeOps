import pytest
from unittest.mock import patch
from services.t5_service import correct_dockerfile


def test_correct_dockerfile_valid(mock_tokenizer, mock_t5_model, mock_genai, t5_mock_db_session,mock_scan_history):
    """Test successful Dockerfile correction."""
    with patch("services.t5_service.AutoTokenizer.from_pretrained", return_value=mock_tokenizer), \
            patch("services.t5_service.AutoModelForSeq2SeqLM.from_pretrained", return_value=mock_t5_model):
        result = correct_dockerfile(1, "FROM ubuntu\nRUN apt update")

        assert result["scan_id"] == 1  # Now passes
        assert result["correction"] == "fixed Dockerfile content"  # From mock.decode
        assert "Line 1: Fixed security issue..." in result["explanation"]  # From mock_genai
        t5_mock_db_session.add.assert_called_once()
        t5_mock_db_session.commit.assert_called_once()


def test_correct_dockerfile_empty_input():
    """Test with empty Dockerfile input."""
    with pytest.raises(ValueError, match="Le champ 'dockerfile' est requis"):
        correct_dockerfile(1, "")


def test_correct_dockerfile_gemini_error(mock_tokenizer, mock_t5_model, t5_mock_db_session):
    """Test with Gemini API error (fallback explanation)."""
    with patch("services.t5_service.genai.GenerativeModel.generate_content",
               side_effect=Exception("API error")), \
            patch("services.t5_service.AutoTokenizer.from_pretrained", return_value=mock_tokenizer), \
            patch("services.t5_service.AutoModelForSeq2SeqLM.from_pretrained", return_value=mock_t5_model):
        result = correct_dockerfile(1, "FROM ubuntu\nRUN apt update")

        assert "[Erreur Gemini]" in result["explanation"]


def test_correct_dockerfile_general_error(t5_mock_db_session, mock_scan_history):
    """Test general RuntimeError handling."""
    # Mock tokenizer to raise during use (simulate load failure)
    with patch("services.t5_service.tokenizer") as mock_tok:
        mock_tok.side_effect = Exception("Tokenizer error")
        with pytest.raises(RuntimeError, match="Failed to process Dockerfile: Tokenizer error"):
            correct_dockerfile(1, "FROM ubuntu\nRUN apt update")

        t5_mock_db_session.rollback.assert_called_once()