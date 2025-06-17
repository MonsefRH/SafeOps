from flask import Flask
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os

from routes.sempgrep import semgrep_bp
from routes.History import history_bp
from routes.user_routes import user_bp
from routes.github_routes import github_bp
from routes.google_routes import google_bp
from routes.dashboard_routes import dashboard_bp
from routes.scan_routes import scan_bp
from routes.checkov import checkov_bp
from routes.risks import risks_bp

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)

# JWT configuration
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
if not app.config["JWT_SECRET_KEY"]:
    raise RuntimeError("Erreur : JWT_SECRET_KEY n'est pas défini dans le fichier .env")
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

if __name__ == "__main__":
    app.run(debug=True, port=5000)