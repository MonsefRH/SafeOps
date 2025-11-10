from flask import Flask
from flask.testing import FlaskClient
from flask_jwt_extended import JWTManager
import sys
from pathlib import Path
from datetime import timedelta
# service fixtures
from fixtures.user_fixtures import *
from fixtures.t5_fixtures import *
from fixtures.risks_fixtures import *
from fixtures.admin_fixtures import *
from fixtures.checkov_fixtures import *
from fixtures.semgrep_fixtures import *
from fixtures.dashboard_fixtures import *
from fixtures.fullscan_fixtures import *
from fixtures.history_fixtures import *
from fixtures.notification_fixtures import *
from fixtures.report_fixtures import *
from fixtures.github_fixtures import *
from fixtures.google_fixtures import *





# Add project root to Python path
project_root = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(project_root))

from utils.db import db, init_db, bcrypt
from services.user_service import login_attempts 

@pytest.fixture(scope="function")
def app() -> Flask:
    """Create Flask app for testing."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = "test-secret"
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)

    # Initialize extensions
    init_db(app)
    jwt = JWTManager(app)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
    
    # Reset globals
    login_attempts.clear()

@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """Flask test client for route tests."""
    return app.test_client()

@pytest.fixture(autouse=True)
def reset_login_attempts():
    """Reset login attempts before each test."""
    login_attempts.clear()
    yield
    login_attempts.clear()