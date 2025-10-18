import pytest
from backend.routes.user_routes import user_bp
from backend.fixtures.user_fixtures import create_test_user, create_pending_user
from backend.utils.db import db
from datetime import datetime, timedelta, timezone

@pytest.fixture(scope="function")
def app_with_blueprint(app):
    """Register user_bp with the test app."""
    app.register_blueprint(user_bp)
    return app

def test_register_route_valid(client, app_with_blueprint, mock_bcrypt, mock_time):
    """Test successful /register endpoint."""
    response = client.post("/register", json={
        "name": "Test User",
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Verification code sent to your email"
    with app_with_blueprint.app_context():
        pending_user = db.session.query(db.Model).filter_by(email="test@example.com").first()
        assert pending_user is not None
        assert pending_user.name == "Test User"

def test_register_route_invalid_input(client, app_with_blueprint):
    """Test /register with invalid input."""
    response = client.post("/register", json={
        "name": "",
        "email": "invalid",
        "password": "short"
    })
    assert response.status_code == 400
    data = response.get_json()
    assert "Invalid input" in data["error"]

def test_verify_code_route_valid(client, app_with_blueprint, mock_jwt, mock_bcrypt, mock_time):
    """Test successful /verify-code endpoint."""
    with app_with_blueprint.app_context():
        create_pending_user(email="test@example.com", code="123456")
    response = client.post("/verify-code", json={
        "email": "test@example.com",
        "code": "123456"
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data["message"] == "Registration successful"
    assert data["access_token"] == "fake_access_token"
    assert data["refresh_token"] == "fake_refresh_token"
    with app_with_blueprint.app_context():
        user = db.session.query(db.Model).filter_by(email="test@example.com").first()
        assert user is not None
        assert user.name == "Test User"

def test_verify_code_route_expired(client, app_with_blueprint, mock_time):
    """Test /verify-code with expired code."""
    with app_with_blueprint.app_context():
        create_pending_user(email="test@example.com", code="123456", expires_at=datetime.now(timezone.utc) - timedelta(minutes=1))
    response = client.post("/verify-code", json={
        "email": "test@example.com",
        "code": "123456"
    })
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "Verification code has expired"

def test_login_route_valid(client, app_with_blueprint, mock_jwt, mock_bcrypt, mock_time):
    """Test successful /login endpoint."""
    with app_with_blueprint.app_context():
        create_test_user(email="test@example.com", password="hashed_pass")
    response = client.post("/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Login successful"
    assert data["access_token"] == "fake_access_token"

def test_login_route_blocked_ip(client, app_with_blueprint, mock_time):
    """Test /login with blocked IP."""
    from backend.services.user_service import login_attempts
    login_attempts["127.0.0.1"] = {
        "count": 5,
        "last_attempt": datetime.now(timezone.utc),
        "blocked_until": datetime.now(timezone.utc) + timedelta(minutes=4)
    }
    response = client.post("/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 429
    data = response.get_json()
    assert data["error"] == "Too many failed attempts. Try again later."

def test_set_password_route_valid(client, app_with_blueprint, mock_jwt, mock_bcrypt, mock_time):
    """Test successful /set-password endpoint."""
    with app_with_blueprint.app_context():
        create_test_user(email="test@example.com", password="old_pass")
    headers = {"Authorization": "Bearer fake_access_token"}
    response = client.post("/set-password", json={"password": "newpass123"}, headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Password set successfully"

def test_set_password_route_unauthorized(client, app_with_blueprint):
    """Test /set-password without JWT."""
    response = client.post("/set-password", json={"password": "newpass123"})
    assert response.status_code == 401  # Flask-JWT-Extended returns 401 for missing token

def test_refresh_route_valid(client, app_with_blueprint, mock_jwt, mock_time):
    """Test successful /refresh endpoint."""
    headers = {"Authorization": "Bearer fake_refresh_token"}
    response = client.post("/refresh", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["access_token"] == "fake_access_token"

def test_refresh_route_unauthorized(client, app_with_blueprint):
    """Test /refresh without refresh token."""
    response = client.post("/refresh")
    assert response.status_code == 401