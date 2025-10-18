import pytest
from pydantic import ValidationError
from schemas.user_dto import (
    RegisterRequest, VerifyCodeRequest, LoginRequest, SetPasswordRequest,
    RegisterResponse, VerifyCodeResponse, LoginResponse, SetPasswordResponse,
    RefreshResponse, ErrorResponse, UserResponse
)

def test_register_request_valid():
    """Test valid RegisterRequest."""
    data = {"name": "Test User", "email": "test@example.com", "password": "pass123"}
    req = RegisterRequest(**data)
    assert req.name == "Test User"
    assert req.email == "test@example.com"
    assert req.password == "pass123"

@pytest.mark.parametrize(
    "data, expected_field, expected_msg",
    [
        ({"name": "", "email": "test@example.com", "password": "pass123"}, "name", "String should have at least 1 character"),  # Min length
        ({"name": "Test", "email": "invalid", "password": "pass123"}, "email", "value is not a valid email address: An email address must have an @-sign."),  # EmailStr
        ({"name": "Test", "email": "test@example.com", "password": "pass"}, "password", "String should have at least 5 characters"),  # Min length
        ({"name": "   ", "email": "test@example.com", "password": "pass123"}, "name", "Name cannot be empty or whitespace-only"),  # Custom validator
    ]
)
def test_register_request_invalid(data, expected_field, expected_msg):
    """Test invalid RegisterRequest."""
    with pytest.raises(ValidationError) as exc_info:
        RegisterRequest(**data)

    error_details = exc_info.value.errors()[0]
    assert error_details["loc"] == (expected_field,)
    assert expected_msg in str(error_details["msg"])

def test_verify_code_request_valid():
    """Test valid VerifyCodeRequest."""
    data = {"email": "test@example.com", "code": "123456"}
    req = VerifyCodeRequest(**data)
    assert req.email == "test@example.com"
    assert req.code == "123456"


@pytest.mark.parametrize("data, expected_field, expected_msg", [
    ({"email":"testexample.com", "code":"123456"}, "email", "value is not a valid email address: An email address must have an @-sign."),
    ({"email":"", "code":"123456"}, "email", "value is not a valid email address: An email address must have an @-sign."),
    ({"email":"test@example.com", "code":""}, "code", "String should have at least 6 characters"),
    ({"email":"test@example.com", "code":"12345"}, "code", "String should have at least 6 characters"),
])
def test_verify_code_request_invalid(data, expected_field, expected_msg):
    """Test invalid VerifyCodeRequest."""
    with pytest.raises(ValidationError) as exc_info:
        VerifyCodeRequest(**data)
    error_details = exc_info.value.errors()[0]
    assert error_details["loc"] == (expected_field,)
    assert expected_msg in str(error_details["msg"])

def test_login_request_valid():
    """Test valid LoginRequest."""
    data = {"email": "test@example.com", "password": "pass123"}
    req = LoginRequest(**data)
    assert req.email == "test@example.com"
    assert req.password == "pass123"

@pytest.mark.parametrize("email, password ,error_expected", [
    ("testexample.com", "pass123", "value is not a valid email address: An email address must have an @-sign."),
    ("@", "pass123", "value is not a valid email address: There must be something before the @-sign."),
    ("", "pass123", "value is not a valid email address: An email address must have an @-sign."),
    ("test@example.com", "pass", "String should have at least 5 characters"),
])
def test_login_request_invalid(email,password,error_expected):
    """Test invalid LoginRequest."""
    with pytest.raises(ValidationError) as exc_info:
        LoginRequest(email=email, password=password)
    assert error_expected in str(exc_info.value)

def test_set_password_request_valid():
    """Test valid SetPasswordRequest."""
    data = {"password": "newpass123"}
    req = SetPasswordRequest(**data)
    assert req.password == "newpass123"

def test_set_password_request_invalid():
    """Test invalid SetPasswordRequest."""
    with pytest.raises(ValidationError) as exc_infos:
        SetPasswordRequest(password="")
    assert "String should have at least 5 characters" in str(exc_infos.value)

def test_response_models():
    """Test response DTOs serialization."""
    user_response = UserResponse(id=1, name="Test", email="test@example.com", role="user")
    assert user_response.model_dump() == {"id": 1, "name": "Test", "email": "test@example.com", "role": "user"}

    register_response = RegisterResponse(message="Verification code sent")
    assert register_response.model_dump() == {"message": "Verification code sent"}

    verify_response = VerifyCodeResponse(
        message="Registration successful",
        access_token="fake_token",
        refresh_token="fake_refresh",
        user=user_response
    )
    assert verify_response.model_dump()["access_token"] == "fake_token"

    login_response = LoginResponse(
        message="Login successful",
        access_token="fake_token",
        refresh_token="fake_refresh",
        user=user_response
    )
    assert login_response.model_dump()["message"] == "Login successful"

    set_password_response = SetPasswordResponse(message="Password set successfully")
    assert set_password_response.model_dump() == {"message": "Password set successfully"}

    refresh_response = RefreshResponse(access_token="fake_token")
    assert refresh_response.model_dump() == {"access_token": "fake_token"}

    error_response = ErrorResponse(error="Invalid input", details="Missing field")
    assert error_response.model_dump() == {"error": "Invalid input", "details": "Missing field"}