import uuid
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from utils.security import token_required
from utils.database import get_ambulance_requests_collection
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
    now_utc = datetime.now(timezone.utc)
    
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

    req_doc = {
        "_id": request_id,
        "id": request_id,
        "user_id": user_id,
        "patient_name": patient_name,
        "contact_number": contact_number,
        "emergency_type": emergency_type,
        "current_location": current_location,
        "additional_details": additional_details,
        "status": "REQUESTED",
        "created_at": now_utc
    }

    try:
        col = get_ambulance_requests_collection()
        if col is not None:
            col.insert_one(req_doc)
    except Exception as e:
        print(f"[Ambulance Request MongoDB error]: {e}")

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
    Returns user's past ambulance assistance requests from MongoDB.
    """
    user_id = current_user["id"]
    requests_list = []

    try:
        col = get_ambulance_requests_collection()
        if col is not None:
            docs = list(col.find({"user_id": user_id}).sort("created_at", -1))
            for doc in docs:
                requests_list.append({
                    "id": str(doc.get("id") or doc.get("_id")),
                    "user_id": doc.get("user_id"),
                    "patient_name": doc.get("patient_name", ""),
                    "contact_number": doc.get("contact_number", ""),
                    "emergency_type": doc.get("emergency_type", ""),
                    "current_location": doc.get("current_location", ""),
                    "additional_details": doc.get("additional_details", ""),
                    "status": doc.get("status", "REQUESTED"),
                    "created_at": doc.get("created_at").isoformat() if hasattr(doc.get("created_at"), "isoformat") else str(doc.get("created_at", ""))
                })
    except Exception as e:
        print(f"[Ambulance List MongoDB error]: {e}")

    return jsonify({
        "success": True,
        "requests": requests_list
    }), 200
