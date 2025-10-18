import re
import random
import string
from datetime import datetime, timedelta, timezone
import logging
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, create_refresh_token
from sqlalchemy.exc import SQLAlchemyError
from utils.db import db
from models.user import User
from models.pending_user import PendingUser
from services.email_template import send_verification_email
import pytz

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s:%(name)s: %(message)s',
    handlers=[logging.FileHandler('user_app.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

bcrypt = Bcrypt()

# In-memory store for login attempts
login_attempts = {}
CODE_EXPIRATION = timedelta(minutes=10)
MAX_ATTEMPTS = 5
BLOCK_DURATION = timedelta(minutes=4)

def generate_verification_code():
    """Generate a 6-digit verification code."""
    return ''.join(random.choices(string.digits, k=6))

def register_user(name, email, password):
    """Register a new user and send verification email."""
    if not name or not email or not password:
        logger.error("Missing required fields for registration")
        raise ValueError("All fields are required")

    email_regex = r"[^@]+@[^@]+\.[^@]+"
    if not re.match(email_regex, email):
        logger.error(f"Invalid email address: {email}")
        raise ValueError("Invalid email address")

    if len(password) < 5:
        logger.error("Password too short")
        raise ValueError("Password must be at least 5 characters long")

    name = name.strip()
    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    # Move duplicate checks OUTSIDE try to avoid catching
    if User.query.filter((User.email == email) | (User.name == name)).first():
        logger.error(f"User with email {email} or name {name} already exists")
        raise ValueError("A user with this email or name already exists")

    if PendingUser.query.filter_by(email=email).first():
        logger.error(f"Verification request pending for email {email}")
        raise ValueError("A verification request for this email is already pending")
    try:
        # Store in pending_users
        verification_code = generate_verification_code()
        expires_at = datetime.now(timezone.utc) + CODE_EXPIRATION
        pending_user = PendingUser(
            name=name,
            email=email,
            password=hashed_password,
            verification_code=verification_code,
            expires_at=expires_at
        )
        db.session.add(pending_user)
        db.session.commit()

        # Send verification email
        if not send_verification_email(email, name, verification_code):
            db.session.delete(pending_user)
            db.session.commit()
            logger.error(f"Failed to send verification email to {email}")
            raise RuntimeError("Failed to send verification email")

        logger.info(f"Verification code sent to {email}")
        return {"message": "Verification code sent to your email"}

    except Exception as e:
        logger.error(f"Registration failed for email {email}: {str(e)}")
        db.session.rollback()
        raise

def verify_code(email, code):
    """Verify the code and create a user account."""
    if not email or not code:
        logger.error("Missing email or verification code")
        raise ValueError("Email and verification code are required")

    pending_user = PendingUser.query.filter_by(email=email).first()
    if not pending_user:
        logger.error(f"No pending registration for email {email}")
        raise ValueError("No pending registration found for this email")
    if code != pending_user.verification_code:
        logger.error(f"Invalid verification code for email {email}")
        raise ValueError("Invalid verification code")
    expires_at_aware = pytz.utc.localize(
        pending_user.expires_at) if pending_user.expires_at.tzinfo is None else pending_user.expires_at
    if datetime.now(timezone.utc) > expires_at_aware:
        db.session.delete(pending_user)
        db.session.commit()
        logger.error(f"Verification code expired for email {email}")
        raise ValueError("Verification code has expired")

    try:
        # Move to users
        user = User(
            name=pending_user.name,
            email=pending_user.email,
            password=pending_user.password,
            role="user"
        )
        db.session.add(user)
        db.session.flush()  # Get user.id

        # Delete from pending_users
        db.session.delete(pending_user)
        db.session.commit()

        # Generate JWT tokens
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))

        logger.info(f"User registered successfully: {email}")
        return {
            "message": "Registration successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {"id": user.id, "name": user.name, "email": user.email, "role": user.role}
        }

    except Exception as e:
        logger.error(f"Verification failed for email {email}: {str(e)}")
        db.session.rollback()
        raise RuntimeError("Verification failed")

def login_user(ip, email, password):
    """Authenticate a user and return JWT tokens."""
    now = datetime.now(timezone.utc)
    if ip not in login_attempts:
        login_attempts[ip] = {"count": 0, "last_attempt": now, "blocked_until": None}

    attempt = login_attempts[ip]
    if attempt["blocked_until"] and now < attempt["blocked_until"]:
        logger.error(f"IP {ip} blocked until {attempt['blocked_until']}")
        raise ValueError("Too many failed attempts. Try again later.")

    if not email or not password:
        logger.error("Missing email or password for login")
        raise ValueError("Email and password are required.")

    email_regex = r"[^@]+@[^@]+\.[^@]+"
    if not re.match(email_regex, email):
        logger.error(f"Invalid email address: {email}")
        raise ValueError("Invalid email address.")

    if len(password) < 5:
        logger.error("Password too short for login")
        raise ValueError("Password must be at least 5 characters long.")

    try:
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_attempts[ip] = {"count": 0, "last_attempt": None, "blocked_until": None}
            access_token = create_access_token(identity=str(user.id))
            refresh_token = create_refresh_token(identity=str(user.id))
            logger.info(f"Login successful for email {email}")
            return {
                "message": "Login successful",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": {"id": user.id, "name": user.name, "email": user.email, "role": user.role}
            }
        else:
            attempt["count"] += 1
            attempt["last_attempt"] = now
            if attempt["count"] >= MAX_ATTEMPTS:
                attempt["blocked_until"] = now + BLOCK_DURATION
                logger.error(f"IP {ip} blocked due to too many failed attempts")
                raise ValueError("Too many attempts. Account temporarily blocked.")
            logger.error(f"Invalid credentials for email {email}")
            raise ValueError("Invalid credentials")

    except (SQLAlchemyError, OSError) as e:
        logger.error(f"Login failed for email {email}: {str(e)}")
        db.session.rollback()
        raise RuntimeError("Internal server error")

def set_password(user_id, password):
    """Set a new password for the user."""
    if not password:
        logger.error("Missing password for set_password")
        raise ValueError("Password is required")

    if len(password) < 5:
        logger.error("Password too short for set_password")
        raise ValueError("Password must be at least 5 characters long")

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    user = User.query.get(user_id)
    if not user:
        logger.error(f"User not found: {user_id}")
        raise ValueError("User not found")
    try:
        user.password = hashed_password
        db.session.commit()
        logger.info(f"Password set successfully for user_id {user_id}")
        return {"message": "Password set successfully"}

    except Exception as e:
        logger.error(f"Failed to set password for user_id {user_id}: {str(e)}")
        db.session.rollback()
        raise RuntimeError("Failed to set password")

def refresh_token(user_id):
    """Generate a new access token using a refresh token."""
    try:
        new_access_token = create_access_token(identity=user_id)
        logger.info(f"Token refreshed for user_id {user_id}")
        return {"access_token": new_access_token}
    except Exception as e:
        logger.error(f"Token refresh failed for user_id {user_id}: {str(e)}")
        raise RuntimeError("Token refresh failed")