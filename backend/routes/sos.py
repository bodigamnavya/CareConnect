import uuid
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from utils.security import token_required
from utils.database import get_sos_events_collection
from utils.validators import sanitize_string

sos_bp = Blueprint("sos_bp", __name__)

@sos_bp.route("/api/sos", methods=["POST"])
@token_required
def create_sos(current_user):
    """
    Emergency SOS event triggering endpoint.
    Saves event to MongoDB sos_events collection.
    """
    data = request.get_json(silent=True) or {}
    user_id = current_user["id"]
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    message = sanitize_string(data.get("message", "Emergency! I need medical assistance."))

    sos_id = f"sos_{uuid.uuid4().hex[:16]}"
    now_utc = datetime.now(timezone.utc)

    try:
        col = get_sos_events_collection()
        if col is not None:
            col.insert_one({
                "_id": sos_id,
                "id": sos_id,
                "user_id": user_id,
                "latitude": latitude,
                "longitude": longitude,
                "message": message,
                "status": "ACTIVE",
                "created_at": now_utc
            })
    except Exception as ex:
        print(f"[SOS Event MongoDB error]: {ex}")

    return jsonify({
        "success": True,
        "message": "Emergency SOS activated successfully! Emergency broadcast logged.",
        "sos_id": sos_id,
        "status": "ACTIVE"
    }), 201

@sos_bp.route("/api/sos/history", methods=["GET"])
@token_required
def sos_history(current_user):
    """
    Returns user's SOS emergency trigger history from MongoDB.
    """
    user_id = current_user["id"]
    events = []

    try:
        col = get_sos_events_collection()
        if col is not None:
            mongo_events = list(col.find({"user_id": user_id}).sort("created_at", -1))
            for ev in mongo_events:
                events.append({
                    "id": str(ev.get("id") or ev.get("_id", "")),
                    "user_id": ev.get("user_id", user_id),
                    "latitude": ev.get("latitude"),
                    "longitude": ev.get("longitude"),
                    "message": ev.get("message", ""),
                    "status": ev.get("status", "ACTIVE"),
                    "created_at": ev.get("created_at").isoformat() if isinstance(ev.get("created_at"), datetime) else str(ev.get("created_at", ""))
                })
    except Exception as ex:
        print(f"[SOS History MongoDB error]: {ex}")

    return jsonify({
        "success": True,
        "events": events
    }), 200
