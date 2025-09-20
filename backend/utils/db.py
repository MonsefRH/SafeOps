from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt

# Load environment variables
load_dotenv()

db = SQLAlchemy()
bcrypt = Bcrypt()

# Function to initialize database configuration and create default admin user
def init_db(app):
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize SQLAlchemy with the app
    db.init_app(app)
    bcrypt.init_app(app)

    # Create tables and default admin user
    with app.app_context():
        try:
            db.create_all()
            create_default_admin()
            print("Database tables and default admin user created successfully.")
        except Exception as e:
            print(f"❌ Error creating database tables or admin user: {e}")
            raise

def create_default_admin():
    """Create a default admin user if it doesn't exist."""
    from models.user import User
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    admin_name = "Admin"
    
    # Check if admin user already exists
    if not User.query.filter_by(email=admin_email).first():
        hashed_password = bcrypt.generate_password_hash(admin_password).decode("utf-8")
        admin_user = User(
            name=admin_name,
            email=admin_email,
            password=hashed_password,
            role="admin"
        )
        db.session.add(admin_user)
        db.session.commit()
        print(f"Default admin user created: {admin_email}")
    else:
        print(f"Admin user with email {admin_email} already exists.")