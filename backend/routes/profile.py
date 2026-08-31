import uuid
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from bson import ObjectId
from utils.database import query_db, execute_db
from utils.security import token_required, hash_password
from utils.validators import sanitize_string, validate_password

profile_bp = Blueprint("profile_bp", __name__)

@profile_bp.route("/api/profile", methods=["GET"])
@token_required
def get_profile(current_user):
    user_id = current_user["id"]

    # 1. Try MongoDB first
    try:
        from utils.mongo import get_mongo_db
        db = get_mongo_db()
        if db is not None:
            user_doc = None
            try:
                user_doc = db["users"].find_one({"_id": ObjectId(user_id)})
            except Exception:
                user_doc = db["users"].find_one({"_id": user_id})
            if not user_doc and current_user.get("email"):
                user_doc = db["users"].find_one({"email": current_user["email"]})
            if user_doc:
                return jsonify({
                    "success": True,
                    "profile": {
                        "id": str(user_doc.get("_id", user_id)),
                        "name": user_doc.get("name", ""),
                        "email": user_doc.get("email", ""),
                        "phone": user_doc.get("phone", ""),
                        "blood_group": user_doc.get("blood_group", ""),
                        "emergency_contact": user_doc.get("emergency_contact", ""),
                        "emergency_phone": user_doc.get("emergency_phone", ""),
                        "allergies": user_doc.get("allergies", ""),
                        "medications": user_doc.get("medications", ""),
                        "conditions": user_doc.get("conditions", ""),
                        "created_at": str(user_doc.get("created_at", ""))
                    }
                }), 200
    except Exception:
        pass

    # 2. Fallback to SQL
    user = query_db(
        "SELECT id, name, email, phone, blood_group, emergency_contact, emergency_phone, allergies, medications, conditions, created_at FROM users WHERE id = ?",
        (user_id,), one=True
    )
    if user:
        return jsonify({
            "success": True,
            "profile": user
        }), 200

    # 3. Fallback to current_user token payload
    return jsonify({
        "success": True,
        "profile": current_user
    }), 200

@profile_bp.route("/api/profile", methods=["PUT"])
@token_required
def update_profile(current_user):
    user_id = current_user["id"]
    data = request.get_json(silent=True) or {}

    name = sanitize_string(data.get("name", current_user.get("name", "")))
    phone = sanitize_string(data.get("phone", current_user.get("phone") or ""))
    blood_group = sanitize_string(data.get("blood_group", current_user.get("blood_group") or ""))
    emergency_contact = sanitize_string(data.get("emergency_contact", current_user.get("emergency_contact") or ""))
    emergency_phone = sanitize_string(data.get("emergency_phone", current_user.get("emergency_phone") or ""))
    allergies = sanitize_string(data.get("allergies", current_user.get("allergies") or ""))
    medications = sanitize_string(data.get("medications", current_user.get("medications") or ""))
    conditions = sanitize_string(data.get("conditions", current_user.get("conditions") or ""))
    new_password = data.get("new_password", "")

    now_iso = datetime.now(timezone.utc).isoformat()
    pwd_hash = None

    if new_password:
        valid_pass, pass_msg = validate_password(new_password)
        if not valid_pass:
            return jsonify({"success": False, "message": pass_msg}), 400
        pwd_hash = hash_password(new_password)

    # 1. Update in MongoDB
    try:
        from utils.mongo import get_mongo_db
        db = get_mongo_db()
        if db is not None:
            update_data = {
                "name": name,
                "phone": phone,
                "blood_group": blood_group,
                "emergency_contact": emergency_contact,
                "emergency_phone": emergency_phone,
                "allergies": allergies,
                "medications": medications,
                "conditions": conditions,
                "updated_at": datetime.now(timezone.utc)
            }
            if pwd_hash:
                update_data["password_hash"] = pwd_hash
            try:
                db["users"].update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
            except Exception:
                db["users"].update_one({"_id": user_id}, {"$set": update_data})
            
            # Also sync into MongoDB medical_profiles
            db["medical_profiles"].update_one(
                {"user_id": user_id},
                {"$set": {
                    "user_id": user_id,
                    "blood_group": blood_group,
                    "phone": emergency_phone or phone,
                    "allergies": allergies,
                    "medications": medications,
                    "conditions": conditions,
                    "emergency_contact": emergency_contact,
                    "updated_at": datetime.now(timezone.utc)
                }},
                upsert=True
            )
    except Exception as ex:
        print(f"[Profile Update MongoDB note]: {ex}")

    # 2. Update in SQL if available
    try:
        if pwd_hash:
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
    except Exception:
        pass

    updated_profile = {
        "id": user_id,
        "name": name,
        "email": current_user.get("email", ""),
        "phone": phone,
        "blood_group": blood_group,
        "emergency_contact": emergency_contact,
        "emergency_phone": emergency_phone,
        "allergies": allergies,
        "medications": medications,
        "conditions": conditions
    }

    return jsonify({
        "success": True,
        "message": "Profile updated successfully.",
        "profile": updated_profile
    }), 200

@profile_bp.route("/api/medical-profile", methods=["POST", "GET"])
@token_required
def handle_medical_profile(current_user):
    user_id = current_user["id"]
    
    if request.method == "GET":
        # 1. Check MongoDB
        try:
            from utils.mongo import get_mongo_db
            db = get_mongo_db()
            if db is not None:
                med_doc = db["medical_profiles"].find_one({"user_id": user_id})
                if med_doc:
                    med_doc.pop("_id", None)
                    return jsonify({"success": True, "profile": med_doc}), 200
        except Exception:
            pass

        # 2. Check SQL
        med = query_db("SELECT * FROM medical_profiles WHERE user_id = ?", (user_id,), one=True)
        if not med:
            u = query_db("SELECT blood_group, phone, emergency_contact, emergency_phone, allergies, medications, conditions FROM users WHERE id = ?", (user_id,), one=True)
            if u and u.get("blood_group"):
                return jsonify({"success": True, "profile": u}), 200
            if current_user.get("blood_group"):
                return jsonify({"success": True, "profile": current_user}), 200
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

    # 1. Save in MongoDB
    try:
        from utils.mongo import get_mongo_db
        db = get_mongo_db()
        if db is not None:
            medical_data = {
                "user_id": user_id,
                "blood_group": blood_group,
                "phone": phone,
                "allergies": allergies,
                "medications": medications,
                "conditions": conditions,
                "emergency_contact": emergency_contact,
                "updated_at": datetime.now(timezone.utc)
            }
            db["medical_profiles"].update_one(
                {"user_id": user_id},
                {"$set": medical_data},
                upsert=True
            )
            # Sync user document
            try:
                db["users"].update_one(
                    {"_id": ObjectId(user_id)},
                    {"$set": {
                        "blood_group": blood_group,
                        "emergency_phone": phone,
                        "emergency_contact": emergency_contact,
                        "allergies": allergies,
                        "medications": medications,
                        "conditions": conditions
                    }}
                )
            except Exception:
                db["users"].update_one(
                    {"_id": user_id},
                    {"$set": {
                        "blood_group": blood_group,
                        "emergency_phone": phone,
                        "emergency_contact": emergency_contact,
                        "allergies": allergies,
                        "medications": medications,
                        "conditions": conditions
                    }}
                )
    except Exception as ex:
        print(f"[Save Medical Profile MongoDB note]: {ex}")

    # 2. Save in SQL
    try:
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

        execute_db(
            """
            UPDATE users
            SET blood_group = ?, emergency_phone = ?, emergency_contact = ?, allergies = ?, medications = ?, conditions = ?, updated_at = ?
            WHERE id = ?
            """,
            (blood_group, phone, emergency_contact, allergies, medications, conditions, now_iso, user_id)
        )
    except Exception:
        pass

    return jsonify({
        "success": True,
        "message": "Medical profile saved successfully"
    }), 200

