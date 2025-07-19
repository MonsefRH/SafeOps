from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from utils.db import get_db_connection
import re
from datetime import datetime, timedelta, timezone
from routes.email_template import send_verification_email
import random
import string
import pytz

user_bp = Blueprint("user", __name__)
bcrypt = Bcrypt()

# In-memory store for verification codes (optional, since we use pending_users table)
verification_codes = {}
CODE_EXPIRATION = timedelta(minutes=10)  # 10 minutes
MAX_ATTEMPTS = 5
BLOCK_DURATION = timedelta(minutes=4)
login_attempts = {}

def generate_verification_code():
    return ''.join(random.choices(string.digits, k=6))

@user_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    name, email, password = data.get("name"), data.get("email"), data.get("password")

    if not name or not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    email_regex = r"[^@]+@[^@]+\.[^@]+"
    if not re.match(email_regex, email):
        return jsonify({"error": "Invalid email address"}), 400

    if len(password) < 5:
        return jsonify({"error": "Password must be at least 5 characters long"}), 400

    name = name.strip()
    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        with conn.cursor() as cur:
            # Check if email or name already exists in users
            cur.execute("SELECT id FROM users WHERE email = %s OR name = %s", (email, name))
            if cur.fetchone():
                return jsonify({"error": "A user with this email or name already exists"}), 409

            # Check if email is pending
            cur.execute("SELECT email FROM pending_users WHERE email = %s", (email,))
            if cur.fetchone():
                return jsonify({"error": "A verification request for this email is already pending"}), 409

            # Store in pending_users
            verification_code = generate_verification_code()
            expires_at = datetime.now(timezone.utc) + CODE_EXPIRATION
            cur.execute(
                "INSERT INTO pending_users (name, email, password, verification_code, expires_at) VALUES (%s, %s, %s, %s, %s)",
                (name, email, hashed_password, verification_code, expires_at)
            )
            conn.commit()

            # Send verification email
            if not send_verification_email(email, name, verification_code):
                return jsonify({"error": "Failed to send verification email"}), 500

            return jsonify({"message": "Verification code sent to your email"}), 200

    except Exception as e:
        print(f"❌ Error during registration: {e}")
        return jsonify({"error": "Registration failed"}), 500

    finally:
        conn.close()

@user_bp.route("/verify-code", methods=["POST"])
def verify_code():
    data = request.get_json()
    email, code = data.get("email"), data.get("code")

    if not email or not code:
        return jsonify({"error": "Email and verification code are required"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        with conn.cursor() as cur:
            # Check pending_users
            cur.execute(
                "SELECT name, email, password, verification_code, expires_at FROM pending_users WHERE email = %s",
                (email,)
            )
            pending_user = cur.fetchone()

            if not pending_user:
                return jsonify({"error": "No pending registration found for this email"}), 404

            name, _, hashed_password, stored_code, expires_at = pending_user

            # Convert expires_at to offset-aware datetime (assume stored in UTC)
            expires_at_aware = pytz.utc.localize(expires_at) if expires_at.tzinfo is None else expires_at

            if datetime.now(timezone.utc) > expires_at_aware:
                cur.execute("DELETE FROM pending_users WHERE email = %s", (email,))
                conn.commit()
                return jsonify({"error": "Verification code has expired"}), 400

            if code != stored_code:
                return jsonify({"error": "Invalid verification code"}), 400

            # Move to users
            cur.execute(
                "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s) RETURNING id",
                (name, email, hashed_password, "user")
            )
            user_id = cur.fetchone()[0]

            # Delete from pending_users
            cur.execute("DELETE FROM pending_users WHERE email = %s", (email,))
            conn.commit()

            # Generate JWT tokens
            access_token = create_access_token(identity=str(user_id))
            refresh_token = create_refresh_token(identity=str(user_id))

            return jsonify({
                "message": "Registration successful",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": {"id": user_id, "name": name, "email": email, "role": "user"}
            }), 201

    except Exception as e:
        print(f"❌ Error during code verification: {e}")
        return jsonify({"error": "Verification failed"}), 500

    finally:
        conn.close()

# Existing endpoints (unchanged)
@user_bp.route("/login", methods=["POST"])
def login():
    ip = request.remote_addr
    now = datetime.now(timezone.utc)

    if ip not in login_attempts:
        login_attempts[ip] = {"count": 0, "last_attempt": now, "blocked_until": None}

    attempt = login_attempts[ip]

    if attempt["blocked_until"] and now < attempt["blocked_until"]:
        return jsonify({"error": "Too many failed attempts. Try again later."}), 429

    data = request.get_json()
    email, password = data.get("email"), data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400
    email_regex = r"[^@]+@[^@]+\.[^@]+"
    if not re.match(email_regex, email):
        return jsonify({"error": "Invalid email address."}), 400

    if len(password) < 5:
        return jsonify({"error": "Password must be at least 5 characters long."}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, email, password, role FROM users WHERE email = %s", (email,))
            user = cur.fetchone()

            if user and bcrypt.check_password_hash(user[3], password):
                login_attempts[ip] = {"count": 0, "last_attempt": None, "blocked_until": None}
                access_token = create_access_token(identity=str(user[0]))
                refresh_token = create_refresh_token(identity=str(user[0]))
                return jsonify({
                    "message": "Login successful",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user": {"id": user[0], "name": user[1], "email": user[2], "role": user[4]}
                })
            else:
                attempt["count"] += 1
                attempt["last_attempt"] = now
                if attempt["count"] >= MAX_ATTEMPTS:
                    attempt["blocked_until"] = now + BLOCK_DURATION
                    return jsonify({"error": "Too many attempts. Account temporarily blocked."}), 429
                return jsonify({"error": "Invalid credentials"}), 401

    except Exception as e:
        print(f"❌ Error during login: {e}")
        return jsonify({"error": "Internal server error"}), 500

    finally:
        conn.close()

@user_bp.route("/set-password", methods=["POST"])
@jwt_required()
def set_password():
    user_id = get_jwt_identity()
    data = request.get_json()
    password = data.get("password")

    if not password:
        return jsonify({"error": "Password is required"}), 400

    if len(password) < 5:
        return jsonify({"error": "Password must be at least 5 characters long"}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET password = %s WHERE id = %s",
                (hashed_password, user_id)
            )
            if cur.rowcount == 0:
                return jsonify({"error": "User not found"}), 404
            conn.commit()
            return jsonify({"message": "Password set successfully"}), 200
    except Exception as e:
        print(f"❌ Error setting password: {e}")
        return jsonify({"error": "Failed to set password"}), 500
    finally:
        conn.close()

@user_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=user_id)
    return jsonify({"access_token": new_access_token})