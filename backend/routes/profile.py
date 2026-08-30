import uuid
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
        "SELECT id, name, email, phone, blood_group, emergency_contact, emergency_phone, allergies, medications, conditions, created_at FROM users WHERE id = ?",
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
    allergies = sanitize_string(data.get("allergies", current_user.get("allergies") or ""))
    medications = sanitize_string(data.get("medications", current_user.get("medications") or ""))
    conditions = sanitize_string(data.get("conditions", current_user.get("conditions") or ""))
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
            SET name = ?, phone = ?, blood_group = ?, emergency_contact = ?, emergency_phone = ?, allergies = ?, medications = ?, conditions = ?, password_hash = ?, updated_at = ?
            WHERE id = ?
            """,
            (name, phone, blood_group, emergency_contact, emergency_phone, allergies, medications, conditions, pwd_hash, now_iso, user_id)
        )
    else:
        execute_db(
            """
            UPDATE users 
            SET name = ?, phone = ?, blood_group = ?, emergency_contact = ?, emergency_phone = ?, allergies = ?, medications = ?, conditions = ?, updated_at = ?
            WHERE id = ?
            """,
            (name, phone, blood_group, emergency_contact, emergency_phone, allergies, medications, conditions, now_iso, user_id)
        )

    # Sync into medical_profiles table as well
    existing_med = query_db("SELECT id FROM medical_profiles WHERE user_id = ?", (user_id,), one=True)
    if existing_med:
        execute_db(
            """
            UPDATE medical_profiles
            SET blood_group = ?, phone = ?, allergies = ?, medications = ?, conditions = ?, emergency_contact = ?, updated_at = ?
            WHERE user_id = ?
            """,
            (blood_group, emergency_phone or phone, allergies, medications, conditions, emergency_contact, now_iso, user_id)
        )
    elif blood_group:
        med_id = f"med_{uuid.uuid4().hex[:16]}"
        execute_db(
            """
            INSERT INTO medical_profiles (id, user_id, blood_group, phone, allergies, medications, conditions, emergency_contact, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (med_id, user_id, blood_group, emergency_phone or phone, allergies, medications, conditions, emergency_contact, now_iso, now_iso)
        )

    updated_user = query_db(
        "SELECT id, name, email, phone, blood_group, emergency_contact, emergency_phone, allergies, medications, conditions FROM users WHERE id = ?",
        (user_id,), one=True
    )

    return jsonify({
        "success": True,
        "message": "Profile updated successfully.",
        "profile": updated_user
    }), 200

@profile_bp.route("/api/medical-profile", methods=["POST", "GET"])
@token_required
def handle_medical_profile(current_user):
    user_id = current_user["id"]
    
    if request.method == "GET":
        med = query_db("SELECT * FROM medical_profiles WHERE user_id = ?", (user_id,), one=True)
        if not med:
            u = query_db("SELECT blood_group, phone, emergency_contact, emergency_phone, allergies, medications, conditions FROM users WHERE id = ?", (user_id,), one=True)
            if u and u.get("blood_group"):
                return jsonify({"success": True, "profile": u}), 200
            return jsonify({"success": False, "message": "Medical profile not found."}), 404
        return jsonify({"success": True, "profile": med}), 200

    # POST
    data = request.get_json(silent=True) or {}
    blood_group = sanitize_string(data.get("blood_group", ""))
    phone = sanitize_string(data.get("phone", ""))
    allergies = sanitize_string(data.get("allergies", ""))
    medications = sanitize_string(data.get("medications", ""))
    conditions = sanitize_string(data.get("conditions", ""))
    emergency_contact = sanitize_string(data.get("emergency_contact", ""))

    if not blood_group:
        return jsonify({"success": False, "message": "Blood group is required"}), 400
    if not phone:
        return jsonify({"success": False, "message": "Emergency phone is required"}), 400
    if not emergency_contact:
        return jsonify({"success": False, "message": "Emergency contact is required"}), 400

    now_iso = datetime.now(timezone.utc).isoformat()
    existing_med = query_db("SELECT id FROM medical_profiles WHERE user_id = ?", (user_id,), one=True)
    if existing_med:
        execute_db(
            """
            UPDATE medical_profiles
            SET blood_group = ?, phone = ?, allergies = ?, medications = ?, conditions = ?, emergency_contact = ?, updated_at = ?
            WHERE user_id = ?
            """,
            (blood_group, phone, allergies, medications, conditions, emergency_contact, now_iso, user_id)
        )
    else:
        med_id = f"med_{uuid.uuid4().hex[:16]}"
        execute_db(
            """
            INSERT INTO medical_profiles (id, user_id, blood_group, phone, allergies, medications, conditions, emergency_contact, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (med_id, user_id, blood_group, phone, allergies, medications, conditions, emergency_contact, now_iso, now_iso)
        )

    # Also update main user record
    execute_db(
        """
        UPDATE users
        SET blood_group = ?, emergency_phone = ?, emergency_contact = ?, allergies = ?, medications = ?, conditions = ?, updated_at = ?
        WHERE id = ?
        """,
        (blood_group, phone, emergency_contact, allergies, medications, conditions, now_iso, user_id)
    )

    return jsonify({
        "success": True,
        "message": "Medical profile saved successfully"
    }), 200
