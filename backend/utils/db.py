import os
import logging
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from sqlalchemy.exc import IntegrityError

# Chargement des variables d'env (.env + env Docker)
load_dotenv()

# Instances globales
db = SQLAlchemy()
bcrypt = Bcrypt()

log = logging.getLogger(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

def _env(name: str, default: str | None = None) -> str:
    """Récupère une variable d'env avec option de valeur par défaut."""
    val = os.getenv(name, default)
    if val is None or (isinstance(val, str) and val.strip() == ""):
        raise RuntimeError(f"Missing required environment variable: {name}")
    return val

def init_db(app):
    """
    Configure SQLAlchemy/Bcrypt, crée les tables et un admin par défaut.
    Ne passe pas de champ 'verified' si le modèle User ne le possède pas.
    """
    # Compose fournit DB_HOST=postgres et DB_PORT=5432 via docker-compose.yml
    db_user = _env("DB_USER")
    db_password = _env("DB_PASSWORD")
    db_host = _env("DB_HOST")
    db_port = _env("DB_PORT")
    db_name = _env("DB_NAME")

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Init extensions
    db.init_app(app)
    bcrypt.init_app(app)

    log.info(
        "SQLAlchemy connecté (host=%s, port=%s, db=%s, user=%s)",
        db_host, db_port, db_name, db_user
    )

    # Création des tables + admin
    with app.app_context():
        try:
            db.create_all()
            create_default_admin()
            log.info(" Tables et admin par défaut OK.")
        except Exception as e:
            log.exception("❌ Error creating database tables or admin user: %s", e)
            # On relance l'exception pour que le conteneur fail et redémarre
            raise

def create_default_admin():
    """Crée un admin par défaut s'il n'existe pas.
    Compatible même si le modèle User n'a pas de champ 'verified'."""
    from models.user import User  # import local pour éviter les imports circulaires

    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    admin_name = os.getenv("ADMIN_NAME", "Admin")

    existing = User.query.filter_by(email=admin_email).first()
    if existing:
        log.info("Admin déjà présent: %s", admin_email)
        return

    hashed = bcrypt.generate_password_hash(admin_password).decode("utf-8")

    # Ne passer que les colonnes sûres
    admin_user = User(
        name=admin_name,
        email=admin_email,
        password=hashed,
        role="admin",
    )

    # Si un champ de vérification existe, on le positionne proprement
    for field in ("verified", "is_verified", "email_verified"):
        if hasattr(admin_user, field):
            setattr(admin_user, field, False)
            break

    db.session.add(admin_user)
    try:
        db.session.commit()
        log.info(" Admin par défaut créé: %s", admin_email)
    except IntegrityError:
        db.session.rollback()
        log.info("Admin déjà créé en parallèle: %s", admin_email)
