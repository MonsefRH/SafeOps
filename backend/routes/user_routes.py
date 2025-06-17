from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from utils.db import get_db_connection
import re
from datetime import datetime, timedelta, timezone

user_bp = Blueprint("user", __name__)
bcrypt = Bcrypt()

# Dictionary to store login attempts
login_attempts = {}
MAX_ATTEMPTS = 5
BLOCK_DURATION = timedelta(minutes=4)

@user_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    name, email, password = data.get("name"), data.get("email"), data.get("password")

    if not name or not email or not password:
        return jsonify({"error": "Tous les champs sont obligatoires"}), 400

    email_regex = r"[^@]+@[^@]+\.[^@]+"
    if not re.match(email_regex, email):
        return jsonify({"error": "Adresse email invalide"}), 400

    if len(password) < 5:
        return jsonify({"error": "Le mot de passe doit contenir au moins 5 caractères"}), 400

    name = name.strip()
    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Impossible de se connecter à la base de données"}), 500

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users_test WHERE email = %s OR name = %s", (email, name))
            if cur.fetchone():
                return jsonify({"error": "Un compte avec cet email existe déjà"}), 409

            cur.execute(
                "INSERT INTO users_test (name, email, password) VALUES (%s, %s, %s) RETURNING id",
                (name, email, hashed_password)
            )
            user_id = cur.fetchone()[0]
            conn.commit()
            return jsonify({"message": "Inscription réussie", "user_id": user_id}), 201

    except Exception as e:
        print("❌ Erreur lors de l'inscription :", e)
        return jsonify({"error": "Erreur lors de l'inscription"}), 500

    finally:
        conn.close()

@user_bp.route("/login", methods=["POST"])
def login():
    ip = request.remote_addr
    now = datetime.now(timezone.utc)

    if ip not in login_attempts:
        login_attempts[ip] = {"count": 0, "last_attempt": now, "blocked_until": None}

    attempt = login_attempts[ip]

    if attempt["blocked_until"] and now < attempt["blocked_until"]:
        return jsonify({"error": "Trop de tentatives échouées. Réessayez dans quelques minutes."}), 429

    data = request.get_json()
    email, password = data.get("email"), data.get("password")

    if not email or not password:
        return jsonify({"error": "Email et mot de passe sont requis."}), 400
    email_regex = r"[^@]+@[^@]+\.[^@]+"
    if not re.match(email_regex, email):
        return jsonify({"error": "Adresse email invalide."}), 400

    if len(password) < 5:
        return jsonify({"error": "Le mot de passe doit contenir au moins 6 caractères."}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Erreur de connexion à la base de données"}), 500

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, email, password FROM users_test WHERE email = %s", (email,))
            user = cur.fetchone()

            if user and bcrypt.check_password_hash(user[3], password):
                login_attempts[ip] = {"count": 0, "last_attempt": None, "blocked_until": None}
                access_token = create_access_token(identity=str(user[0]))
                refresh_token = create_refresh_token(identity=str(user[0]))
                return jsonify({
                    "message": "Connexion réussie",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user": {"id": user[0], "name": user[1], "email": user[2]}
                })
            else:
                attempt["count"] += 1
                attempt["last_attempt"] = now
                if attempt["count"] >= MAX_ATTEMPTS:
                    attempt["blocked_until"] = now + BLOCK_DURATION
                    return jsonify({"error": "Trop de tentatives. Compte bloqué temporairement."}), 429
                return jsonify({"error": "Identifiants incorrects"}), 401

    except Exception as e:
        print("❌ Erreur lors de la connexion :", e)
        return jsonify({"error": "Erreur interne"}), 500

    finally:
        conn.close()

@user_bp.route("/set-password", methods=["POST"])
@jwt_required()
def set_password():
    user_id = get_jwt_identity()
    data = request.get_json()
    password = data.get("password")

    if not password:
        return jsonify({"error": "Le mot de passe est requis"}), 400

    if len(password) < 5:
        return jsonify({"error": "Le mot de passe doit contenir au moins 5 caractères"}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Erreur de connexion à la base de données"}), 500

    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users_test SET password = %s WHERE id = %s",
                (hashed_password, user_id)
            )
            if cur.rowcount == 0:
                return jsonify({"error": "Utilisateur non trouvé"}), 404
            conn.commit()
            return jsonify({"message": "Mot de passe défini avec succès"}), 200
    except Exception as e:
        print("❌ Erreur lors de la définition du mot de passe :", e)
        return jsonify({"error": "Erreur lors de la définition du mot de passe"}), 500
    finally:
        conn.close()

@user_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=user_id)
    return jsonify({"access_token": new_access_token})