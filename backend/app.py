from flask import Flask
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os

from routes.semgrep import semgrep_bp
from routes.History import history_bp
from routes.user_routes import user_bp
from routes.github_routes import github_bp
from routes.google_routes import google_bp
from routes.dashboard_routes import dashboard_bp
from routes.scan_routes import scan_bp
from routes.checkov import checkov_bp
from routes.risks import risks_bp
from routes.full_scan_routes import full_scan_bp
from routes.t5_base import t5_base_bp
from routes.admin import admin_bp

# Load environment variables
load_dotenv()

app = Flask(__name__)



csrf = CSRFProtect(app)
CORS(app)
bcrypt = Bcrypt(app)

# JWT configuration
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
if not app.config["JWT_SECRET_KEY"]:
    raise RuntimeError("Error: JWT_SECRET_KEY is not defined in the .env file")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600  # 1 hour
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = 86400  # 24 hours
jwt = JWTManager(app)

# Register Blueprints
app.register_blueprint(user_bp, url_prefix="/")
app.register_blueprint(github_bp, url_prefix="/")
app.register_blueprint(google_bp, url_prefix="/")
app.register_blueprint(dashboard_bp, url_prefix="/")
app.register_blueprint(scan_bp, url_prefix="/")
app.register_blueprint(checkov_bp, url_prefix="/")
app.register_blueprint(history_bp, url_prefix="/")
app.register_blueprint(semgrep_bp, url_prefix="/")
app.register_blueprint(risks_bp, url_prefix="/")
app.register_blueprint(full_scan_bp, url_prefix="/")
app.register_blueprint(t5_base_bp, url_prefix="/")
app.register_blueprint(admin_bp, url_prefix="/")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
