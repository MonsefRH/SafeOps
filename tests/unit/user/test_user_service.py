import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta, timezone
from services.user_service import (
    generate_verification_code,
    register_user,
    verify_code,
    login_user,
    set_password,
    refresh_token,
    login_attempts,
    MAX_ATTEMPTS,
    BLOCK_DURATION
)


def test_generate_verification_code():
    """Test generate_verification_code produces a 6-digit code."""
    code = generate_verification_code()
    assert len(code) == 6
    assert code.isdigit()


def test_register_user_valid(mock_db_session, mock_user_query, mock_pending_user_query, mock_bcrypt, mock_email):
    """Test successful user registration."""
    mock_user_query.filter.return_value.first.return_value = None
    mock_pending_user_query.filter_by.return_value.first.return_value = None

    with patch("services.user_service.generate_verification_code", return_value="123456"):
        result = register_user("Test User", "test@example.com", "password123")

    assert result == {"message": "Verification code sent to your email"}
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()
    mock_bcrypt.generate_password_hash.assert_called_once_with("password123")
    mock_email.assert_called_once()


@pytest.mark.parametrize("name, email, password, expected_error", [
    ("", "test@example.com", "pass123", "All fields are required"),
    ("Test", "invalid-email", "pass123", "Invalid email address"),
    ("Test", "test@example.com", "pass", "Password must be at least 5 characters long"),
    ("Test", "test@example.com", "pass123", "A user with this email or name already exists"),
    ("Test", "test@example.com", "pass123", "A verification request for this email is already pending")
])
def test_register_user_invalid_inputs(mock_db_session, mock_user_query, mock_pending_user_query,mock_bcrypt, mock_email, name, email, password,
                                      expected_error):
    """Test registration with invalid inputs or conflicts."""
    if "already exists" in expected_error:
        mock_user_query.filter.return_value.first.return_value = Mock()
        mock_pending_user_query.filter_by.return_value.first.return_value = None
    elif "pending" in expected_error:
        mock_user_query.filter.return_value.first.return_value = None
        mock_pending_user_query.filter_by.return_value.first.return_value = Mock()
    else:
        mock_user_query.filter.return_value.first.return_value = None
        mock_pending_user_query.filter_by.return_value.first.return_value = None

    with pytest.raises(ValueError, match=expected_error):
        register_user(name, email, password)


def test_register_user_email_failure(mock_db_session, mock_user_query, mock_pending_user_query, mock_bcrypt):
    """Test registration when email sending fails."""
    mock_user_query.filter.return_value.first.return_value = None
    mock_pending_user_query.filter_by.return_value.first.return_value = None

    with patch("services.user_service.generate_verification_code", return_value="123456"), \
            patch("services.user_service.send_verification_email", return_value=False):
        with pytest.raises(RuntimeError, match="Failed to send verification email"):
            register_user("Test User", "test@example.com", "password123")

    mock_db_session.delete.assert_called_once()
    mock_db_session.commit.assert_called()


def test_verify_code_valid(mock_db_session, mock_pending_user_query, mock_jwt):
    """Test successful code verification."""
    future_time = datetime.now(timezone.utc) + timedelta(minutes=5)

    mock_pending = Mock()
    mock_pending.email = "test@example.com"
    mock_pending.name = "Test"
    mock_pending.password = b"hashed_pass"
    mock_pending.verification_code = "123456"
    mock_pending.expires_at = future_time

    mock_pending_user_query.filter_by.return_value.first.return_value = mock_pending

    with patch("services.user_service.User") as MockUser:
        mock_user_instance = Mock()
        mock_user_instance.id = 1
        mock_user_instance.name = "Test"
        mock_user_instance.email = "test@example.com"
        mock_user_instance.role = "user"
        MockUser.return_value = mock_user_instance

        result = verify_code("test@example.com", "123456")

    assert result["message"] == "Registration successful"
    assert result["access_token"] == "fake_access_token"
    assert result["refresh_token"] == "fake_refresh_token"
    assert result["user"]["id"] == 1
    mock_db_session.add.assert_called_once()
    mock_db_session.delete.assert_called_once()
    mock_db_session.commit.assert_called_once()


def test_verify_code_expired(mock_db_session, mock_pending_user_query):
    """Test verification with expired code."""
    past_time = datetime.now(timezone.utc) - timedelta(minutes=1)

    mock_pending = Mock()
    mock_pending.email = "test@example.com"
    mock_pending.verification_code = "123456"
    mock_pending.expires_at = past_time

    mock_pending_user_query.filter_by.return_value.first.return_value = mock_pending

    with pytest.raises(ValueError, match="Verification code has expired"):
        verify_code("test@example.com", "123456")

    mock_db_session.delete.assert_called_once()


@pytest.mark.parametrize("email, code, expected_error", [
    ("", "123456", "Email and verification code are required"),
    ("test@example.com", "", "Email and verification code are required"),
    ("test@example.com", "123456", "No pending registration found for this email"),
    ("test@example.com", "wrong", "Invalid verification code")
])
def test_verify_code_invalid(mock_db_session, mock_pending_user_query, email, code, expected_error):
    """Test verification with invalid inputs or codes."""
    if "No pending" in expected_error:
        mock_pending_user_query.filter_by.return_value.first.return_value = None
    elif "Invalid verification" in expected_error:
        future_time = datetime.now(timezone.utc) + timedelta(minutes=5)
        mock_pending = Mock(verification_code="123456", expires_at=future_time)
        mock_pending_user_query.filter_by.return_value.first.return_value = mock_pending

    with pytest.raises(ValueError, match=expected_error):
        verify_code(email, code)


def test_login_user_valid(mock_db_session, mock_user_query, mock_jwt, mock_bcrypt):
    """Test successful login."""
    mock_user = Mock()
    mock_user.id = 1
    mock_user.name = "Test"
    mock_user.email = "test@example.com"
    mock_user.password = b"hashed_pass"
    mock_user.role = "user"

    mock_user_query.filter_by.return_value.first.return_value = mock_user

    result = login_user("127.0.0.1", "test@example.com", "password123")

    assert result["message"] == "Login successful"
    assert result["access_token"] == "fake_access_token"
    assert result["user"]["email"] == "test@example.com"
    assert login_attempts["127.0.0.1"]["count"] == 0
    mock_bcrypt.check_password_hash.assert_called_once_with(b"hashed_pass", "password123")


def test_login_user_blocked_ip():
    """Test login with blocked IP."""
    login_attempts["127.0.0.1"] = {
        "count": MAX_ATTEMPTS,
        "last_attempt": datetime.now(timezone.utc),
        "blocked_until": datetime.now(timezone.utc) + BLOCK_DURATION
    }

    with pytest.raises(ValueError, match="Too many failed attempts"):
        login_user("127.0.0.1", "test@example.com", "password123")


def test_login_user_too_many_attempts(mock_db_session, mock_user_query, mock_bcrypt):
    """Test login with too many failed attempts."""
    login_attempts["127.0.0.1"] = {
        "count": MAX_ATTEMPTS - 1,
        "last_attempt": datetime.now(timezone.utc),
        "blocked_until": None
    }

    mock_user = Mock()
    mock_user.password = b"hashed_pass"
    mock_user_query.filter_by.return_value.first.return_value = mock_user
    mock_bcrypt.check_password_hash.return_value = False

    with pytest.raises(ValueError, match="Too many attempts"):
        login_user("127.0.0.1", "test@example.com", "wrongpass")

    assert login_attempts["127.0.0.1"]["count"] == MAX_ATTEMPTS
    assert login_attempts["127.0.0.1"]["blocked_until"] is not None


@pytest.mark.parametrize("ip, email, password, expected_error", [
    ("127.0.0.1", "", "pass123", "Email and password are required"),
    ("127.0.0.1", "invalid-email", "pass123", "Invalid email address"),
    ("127.0.0.1", "test@example.com", "pass", "Password must be at least 5 characters long"),
    ("127.0.0.1", "test@example.com", "wrongpass", "Invalid credentials")
])
def test_login_user_invalid(mock_db_session, mock_user_query, mock_bcrypt, ip, email, password, expected_error):
    """Test login with invalid inputs or credentials."""
    if "Invalid credentials" in expected_error:
        mock_user_query.filter_by.return_value.first.return_value = None
    elif "Password must be at least" in expected_error:
        mock_user = Mock(password=b"hashed_pass")
        mock_user_query.filter_by.return_value.first.return_value = mock_user
        mock_bcrypt.check_password_hash.return_value = False

    with pytest.raises(ValueError, match=expected_error):
        login_user(ip, email, password)


def test_set_password_valid(mock_db_session, mock_user_query, mock_bcrypt):
    """Test successful password update."""
    mock_user = Mock()
    mock_user.id = 1
    mock_user.password = b"old_pass"

    mock_user_query.get.return_value = mock_user

    result = set_password("1", "newpass123")

    assert result["message"] == "Password set successfully"
    mock_bcrypt.generate_password_hash.assert_called_once_with("newpass123")
    assert mock_user.password == "hashed_pass"
    mock_db_session.commit.assert_called_once()


@pytest.mark.parametrize("user_id, password, expected_error", [
    ("1", "", "Password is required"),
    ("1", "pass", "Password must be at least 5 characters long"),
    ("999", "pass123", "User not found")
])
def test_set_password_invalid(mock_db_session, mock_user_query, user_id, password, expected_error):
    """Test set_password with invalid inputs or non-existent user."""
    if "User not found" in expected_error:
        mock_user_query.get.return_value = None
    else:
        mock_user = Mock(id=1, password=b"old_pass")
        mock_user_query.get.return_value = mock_user

    with pytest.raises(ValueError, match=expected_error):
        set_password(user_id, password)


def test_refresh_token_valid(mock_jwt):
    """Test successful token refresh."""
    result = refresh_token("1")
    assert result["access_token"] == "fake_access_token"


def test_refresh_token_error():
    """Test token refresh failure."""
    with patch("services.user_service.create_access_token", side_effect=Exception("JWT error")):
        with pytest.raises(RuntimeError, match="Token refresh failed"):
            refresh_token("1")