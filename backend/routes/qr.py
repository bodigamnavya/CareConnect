import uuid
import base64
from io import BytesIO
from datetime import datetime, timezone
import qrcode
from flask import Blueprint, request, jsonify
from bson import ObjectId
from utils.security import token_required
from utils.database import query_db, execute_db

qr_bp = Blueprint("qr_bp", __name__)

@qr_bp.route("/api/generate-qr", methods=["GET"])
@token_required
def generate_qr(current_user):
    """
    Generates a secure QR Health Passport token and returns base64 QR PNG.
    """
    user_id = current_user["id"]
    profile = None

    # 1. Check MongoDB first
    try:
        from utils.mongo import get_mongo_db
        db = get_mongo_db()
        if db is not None:
            profile = db["medical_profiles"].find_one({"user_id": user_id})
            if not profile:
                try:
                    profile = db["users"].find_one({"_id": ObjectId(user_id)})
                except Exception:
                    profile = db["users"].find_one({"_id": user_id})
    except Exception:
        pass

    # 2. Check SQL fallback
    if not profile:
        profile = query_db(
            "SELECT * FROM medical_profiles WHERE user_id = ?",
            (user_id,), one=True
        )
    if not profile:
        user_row = query_db(
            "SELECT name, blood_group, phone, emergency_contact, emergency_phone, allergies, medications, conditions FROM users WHERE id = ?",
            (user_id,), one=True
        )
        if user_row and user_row.get("blood_group"):
            profile = user_row
        elif current_user.get("blood_group"):
            profile = current_user

    if not profile:
        return jsonify({
            "success": False,
            "message": "Medical profile not found. Please save your medical profile first."
        }), 404

    qr_token = uuid.uuid4().hex
    record_id = f"qrt_{uuid.uuid4().hex[:16]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    # Save token in MongoDB
    try:
        from utils.mongo import get_mongo_db
        db = get_mongo_db()
        if db is not None:
            db["qr_tokens"].insert_one({
                "token": qr_token,
                "user_id": user_id,
                "created_at": datetime.now(timezone.utc),
                "active": True
            })
    except Exception:
        pass

    # Save token in SQL
    try:
        execute_db(
            "INSERT INTO qr_tokens (id, token, user_id, active, created_at) VALUES (?, ?, ?, 1, ?)",
            (record_id, qr_token, user_id, now_iso)
        )
    except Exception:
        pass

    # Encode medical URL / data in QR
    base_url = request.host_url.rstrip("/")
    scan_url = f"{base_url}/api/qr/view/{qr_token}"

    qr_img = qrcode.make(scan_url)
    buffer = BytesIO()
    qr_img.save(buffer, format="PNG")
    buffer.seek(0)
    qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return jsonify({
        "success": True,
        "message": "QR generated successfully.",
        "qr_code": qr_base64,
        "token": qr_token,
        "view_url": scan_url
    }), 200

@qr_bp.route("/api/qr/view/<token>", methods=["GET"])
def view_qr(token):
    """
    Public emergency endpoint to retrieve critical medical data via scanned QR.
    """
    user_id = None
    profile = None
    user_info = None

    # 1. Search in MongoDB
    try:
        from utils.mongo import get_mongo_db
        db = get_mongo_db()
        if db is not None:
            qr_doc = db["qr_tokens"].find_one({"token": token, "active": True})
            if qr_doc:
                user_id = qr_doc["user_id"]
                profile = db["medical_profiles"].find_one({"user_id": user_id})
                try:
                    user_info = db["users"].find_one({"_id": ObjectId(user_id)})
                except Exception:
                    user_info = db["users"].find_one({"_id": user_id})

                # Log access in MongoDB
                db["access_logs"].insert_one({
                    "user_id": user_id,
                    "access_type": "QR_SCAN",
                    "accessed_at": datetime.now(timezone.utc)
                })
    except Exception:
        pass

    # 2. Search in SQL fallback if not found
    if not profile and not user_info:
        qr_doc = query_db(
            "SELECT * FROM qr_tokens WHERE token = ? AND active = 1",
            (token,), one=True
        )
        if qr_doc:
            user_id = qr_doc["user_id"]
            profile = query_db("SELECT * FROM medical_profiles WHERE user_id = ?", (user_id,), one=True)
            user_info = query_db("SELECT id, name, blood_group, phone, emergency_contact, emergency_phone, allergies, medications, conditions FROM users WHERE id = ?", (user_id,), one=True)
            log_id = f"log_{uuid.uuid4().hex[:16]}"
            execute_db("INSERT INTO access_logs (id, user_id, access_type, accessed_at) VALUES (?, ?, 'QR_SCAN', ?)", (log_id, user_id, datetime.now(timezone.utc).isoformat()))

    if not profile and not user_info:
        return jsonify({
            "success": False,
            "message": "Invalid or inactive QR code, or medical profile not found."
        }), 404

    emergency_data = {
        "patient_name": (user_info.get("name") if user_info else "Patient") or "Patient",
        "blood_group": (profile.get("blood_group") if profile else (user_info.get("blood_group") if user_info else "Not specified")) or "Not specified",
        "emergency_phone": (profile.get("phone") if profile else (user_info.get("emergency_phone") or user_info.get("phone") if user_info else "")) or "",
        "emergency_contact": (profile.get("emergency_contact") if profile else (user_info.get("emergency_contact") if user_info else "")) or "",
        "allergies": (profile.get("allergies") if profile else (user_info.get("allergies") if user_info else "None reported")) or "None reported",
        "medications": (profile.get("medications") if profile else (user_info.get("medications") if user_info else "None reported")) or "None reported",
        "conditions": (profile.get("conditions") if profile else (user_info.get("conditions") if user_info else "None reported")) or "None reported"
    }

    return jsonify({
        "success": True,
        "message": "Emergency medical information",
        "medical_profile": emergency_data
    }), 200

