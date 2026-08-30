import uuid
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from utils.database import query_db, execute_db
from utils.security import hash_password, check_password, generate_jwt, token_required
from utils.validators import validate_email, validate_password, sanitize_string

auth_bp = Blueprint("auth_bp", __name__)

@auth_bp.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    name = sanitize_string(data.get("name", ""))
    email = sanitize_string(data.get("email", "")).lower()
    password = data.get("password", "")

    if not name:
        return jsonify({"success": False, "message": "Full name is required."}), 400

    if not validate_email(email):
        return jsonify({"success": False, "message": "A valid email address is required."}), 400

    valid_pass, pass_msg = validate_password(password)
    if not valid_pass:
        return jsonify({"success": False, "message": pass_msg}), 400

    # Check for existing user
    existing = query_db("SELECT id FROM users WHERE email = ?", (email,), one=True)
    if existing:
        return jsonify({"success": False, "message": "Email is already registered. Please sign in."}), 409

    user_id = f"usr_{uuid.uuid4().hex[:16]}"
    pwd_hash = hash_password(password)
    now_iso = datetime.now(timezone.utc).isoformat()

    execute_db(
        "INSERT INTO users (id, name, email, password_hash, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, name, email, pwd_hash, now_iso, now_iso)
    )

    # Automatically generate JWT token on successful registration
    token = generate_jwt(user_id, email)

    return jsonify({
        "success": True,
        "message": "Registration successful! Welcome to CareConnect.",
        "token": token,
        "user": {
            "id": user_id,
            "name": name,
            "email": email
        }
    }), 201

@auth_bp.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = sanitize_string(data.get("email", "")).lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required."}), 400

    user = query_db("SELECT id, name, email, password_hash, phone, blood_group FROM users WHERE email = ?", (email,), one=True)
    if not user or not check_password(password, user["password_hash"]):
        return jsonify({"success": False, "message": "Invalid email or password."}), 401

    token = generate_jwt(user["id"], user["email"])

    return jsonify({
        "success": True,
        "message": "Login successful.",
        "token": token,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "phone": user.get("phone") or "",
            "blood_group": user.get("blood_group") or ""
        }
    }), 200

@auth_bp.route("/api/logout", methods=["POST"])
def logout():
    return jsonify({"success": True, "message": "Logged out successfully."}), 200
