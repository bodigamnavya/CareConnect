from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from utils.database import query_db, execute_db
from utils.security import token_required, hash_password
from utils.validators import sanitize_string, validate_password

profile_bp = Blueprint("profile_bp", __name__)

@profile_bp.route("/api/profile", methods=["GET"])
@token_required
def get_profile(current_user):
    user_id = current_user["id"]
    user = query_db(
        "SELECT id, name, email, phone, blood_group, emergency_contact, emergency_phone, created_at FROM users WHERE id = ?",
        (user_id,), one=True
    )
    if not user:
        return jsonify({"success": False, "message": "User profile not found."}), 404
        
    return jsonify({
        "success": True,
        "profile": user
    }), 200

@profile_bp.route("/api/profile", methods=["PUT"])
@token_required
def update_profile(current_user):
    user_id = current_user["id"]
    data = request.get_json(silent=True) or {}

    name = sanitize_string(data.get("name", current_user["name"]))
    phone = sanitize_string(data.get("phone", current_user.get("phone") or ""))
    blood_group = sanitize_string(data.get("blood_group", current_user.get("blood_group") or ""))
    emergency_contact = sanitize_string(data.get("emergency_contact", current_user.get("emergency_contact") or ""))
    emergency_phone = sanitize_string(data.get("emergency_phone", current_user.get("emergency_phone") or ""))
    new_password = data.get("new_password", "")

    now_iso = datetime.now(timezone.utc).isoformat()

    if new_password:
        valid_pass, pass_msg = validate_password(new_password)
        if not valid_pass:
            return jsonify({"success": False, "message": pass_msg}), 400
        pwd_hash = hash_password(new_password)
        execute_db(
            """
            UPDATE users 
            SET name = ?, phone = ?, blood_group = ?, emergency_contact = ?, emergency_phone = ?, password_hash = ?, updated_at = ?
            WHERE id = ?
            """,
            (name, phone, blood_group, emergency_contact, emergency_phone, pwd_hash, now_iso, user_id)
        )
    else:
        execute_db(
            """
            UPDATE users 
            SET name = ?, phone = ?, blood_group = ?, emergency_contact = ?, emergency_phone = ?, updated_at = ?
            WHERE id = ?
            """,
            (name, phone, blood_group, emergency_contact, emergency_phone, now_iso, user_id)
        )

    updated_user = query_db(
        "SELECT id, name, email, phone, blood_group, emergency_contact, emergency_phone FROM users WHERE id = ?",
        (user_id,), one=True
    )

    return jsonify({
        "success": True,
        "message": "Profile updated successfully.",
        "profile": updated_user
    }), 200
