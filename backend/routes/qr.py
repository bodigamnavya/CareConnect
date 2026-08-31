import uuid
import base64
from io import BytesIO
from datetime import datetime, timezone
import qrcode
from flask import Blueprint, request, jsonify
from bson import ObjectId
from utils.security import token_required
from utils.database import (
    get_users_collection,
    get_medical_profiles_collection,
    get_qr_tokens_collection,
    get_access_logs_collection
)

qr_bp = Blueprint("qr_bp", __name__)

@qr_bp.route("/api/generate-qr", methods=["GET"])
@token_required
def generate_qr(current_user):
    """
    Generates a secure QR Health Passport token and returns base64 QR PNG.
    """
    user_id = current_user["id"]
    profile = None
    user_info = None

    try:
        med_col = get_medical_profiles_collection()
        users_col = get_users_collection()
        if med_col is not None:
            profile = med_col.find_one({"user_id": user_id})
        if users_col is not None:
            try:
                user_info = users_col.find_one({"_id": ObjectId(user_id)})
            except Exception:
                user_info = users_col.find_one({"_id": user_id})
            if not user_info:
                user_info = users_col.find_one({"id": user_id})
    except Exception as ex:
        print(f"[Generate QR MongoDB error]: {ex}")

    if not profile and user_info and user_info.get("blood_group"):
        profile = user_info
    elif not profile and current_user.get("blood_group"):
        profile = current_user

    if not profile and not user_info:
        return jsonify({
            "success": False,
            "message": "Medical profile not found. Please save your medical profile first."
        }), 404

    qr_token = uuid.uuid4().hex
    now_utc = datetime.now(timezone.utc)

    # Save token in MongoDB
    try:
        qr_col = get_qr_tokens_collection()
        if qr_col is not None:
            qr_col.insert_one({
                "token": qr_token,
                "user_id": user_id,
                "created_at": now_utc,
                "active": True
            })
    except Exception as ex:
        print(f"[QR Token Save error]: {ex}")

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

    try:
        qr_col = get_qr_tokens_collection()
        med_col = get_medical_profiles_collection()
        users_col = get_users_collection()
        log_col = get_access_logs_collection()

        if qr_col is not None:
            qr_doc = qr_col.find_one({"token": token, "active": True})
            if qr_doc:
                user_id = qr_doc["user_id"]
                if med_col is not None:
                    profile = med_col.find_one({"user_id": user_id})
                if users_col is not None:
                    try:
                        user_info = users_col.find_one({"_id": ObjectId(user_id)})
                    except Exception:
                        user_info = users_col.find_one({"_id": user_id})
                    if not user_info:
                        user_info = users_col.find_one({"id": user_id})

                # Log access in MongoDB
                if log_col is not None:
                    log_col.insert_one({
                        "user_id": user_id,
                        "access_type": "QR_SCAN",
                        "accessed_at": datetime.now(timezone.utc)
                    })
    except Exception as ex:
        print(f"[View QR Error]: {ex}")

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
