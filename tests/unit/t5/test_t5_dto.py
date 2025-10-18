import pytest
from pydantic import ValidationError
from schemas.t5_dto import T5Request, T5Response, T5ErrorResponse

def test_t5_request_valid():
    """Test valid T5Request."""
    data = {"dockerfile": "FROM ubuntu\nRUN apt update"}
    req = T5Request(**data)
    assert req.dockerfile == "FROM ubuntu\nRUN apt update"

def test_t5_request_invalid():
    """Test invalid T5Request (missing dockerfile)."""
    with pytest.raises(ValidationError):
        T5Request(dockerfile="")

def test_t5_response_valid():
    """Test valid T5Response serialization."""
    response = T5Response(scan_id=1, correction="fixed code", explanation="explanation")
    assert response.model_dump() == {
        "scan_id": 1,
        "correction": "fixed code",
        "explanation": "explanation"
    }
def test_t5_response_invalid():
    """Test valid T5Response serialization."""
    with pytest.raises(ValidationError):
        T5Response(correction="fixed code", explanation="explanation")


def test_t5_error_response_valid():
    """Test valid T5ErrorResponse serialization."""
    error = T5ErrorResponse(error="Invalid input", details="Missing dockerfile")
    assert error.model_dump() == {
        "error": "Invalid input",
        "details": "Missing dockerfile"
    }

    # Test without details
    error_no_details = T5ErrorResponse(error="Server error")
    assert error_no_details.model_dump() == {
        "error": "Server error",
        "details": None
    }