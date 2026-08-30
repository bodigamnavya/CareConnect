import uuid
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from utils.security import token_required
from utils.database import query_db, execute_db
from utils.validators import sanitize_string

ambulance_bp = Blueprint("ambulance_bp", __name__)

@ambulance_bp.route("/api/ambulance/request", methods=["POST"])
def request_ambulance():
    """
    Emergency ambulance assistance request endpoint.
    Accessible with or without auth token for emergency situations.
    """
    data = request.get_json(silent=True) or {}
    patient_name = sanitize_string(data.get("patient_name", ""))
    contact_number = sanitize_string(data.get("contact_number", "") or data.get("phone", ""))
    emergency_type = sanitize_string(data.get("emergency_type", "General Medical Emergency"))
    current_location = sanitize_string(data.get("current_location", "") or data.get("location", ""))
    additional_details = sanitize_string(data.get("additional_details", "") or data.get("details", ""))

    if not patient_name:
        return jsonify({"success": False, "message": "Patient name is required."}), 400

    if not contact_number:
        return jsonify({"success": False, "message": "Contact number is required."}), 400

    if not current_location:
        return jsonify({"success": False, "message": "Current location is required."}), 400

    request_id = f"amb_{uuid.uuid4().hex[:16]}"
    now_iso = datetime.now(timezone.utc).isoformat()
    
    # Optional user association if auth token present
    user_id = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        try:
            import jwt
            from config import Config
            payload = jwt.decode(token, Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM])
            user_id = payload.get("user_id") or payload.get("id")
        except Exception:
            user_id = None

    execute_db(
        """
        INSERT INTO ambulance_requests (id, user_id, patient_name, contact_number, emergency_type, current_location, additional_details, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'REQUESTED', ?)
        """,
        (request_id, user_id, patient_name, contact_number, emergency_type, current_location, additional_details, now_iso)
    )

    return jsonify({
        "success": True,
        "message": "Ambulance request submitted successfully. Emergency request received. Please contact local emergency services (112 / 911) for immediate life-threatening assistance.",
        "request_id": request_id,
        "status": "REQUESTED",
        "details": {
            "patient_name": patient_name,
            "emergency_type": emergency_type,
            "current_location": current_location
        }
    }), 201

@ambulance_bp.route("/api/ambulance/requests", methods=["GET"])
@token_required
def list_ambulance_requests(current_user):
    """
    Returns user's past ambulance assistance requests.
    """
    user_id = current_user["id"]
    requests = query_db(
        "SELECT * FROM ambulance_requests WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    ) or []

    return jsonify({
        "success": True,
        "requests": requests
    }), 200
