import uuid
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from utils.security import token_required
from utils.database import query_db, execute_db
from utils.validators import sanitize_string

sos_bp = Blueprint("sos_bp", __name__)

@sos_bp.route("/api/sos", methods=["POST"])
@token_required
def create_sos(current_user):
    """
    Emergency SOS event triggering endpoint.
    """
    data = request.get_json(silent=True) or {}
    user_id = current_user["id"]
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    message = sanitize_string(data.get("message", "Emergency! I need medical assistance."))

    sos_id = f"sos_{uuid.uuid4().hex[:16]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    execute_db(
        """
        INSERT INTO sos_events (id, user_id, latitude, longitude, message, status, created_at)
        VALUES (?, ?, ?, ?, ?, 'ACTIVE', ?)
        """,
        (sos_id, user_id, latitude, longitude, message, now_iso)
    )

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
    Returns user's SOS emergency trigger history.
    """
    user_id = current_user["id"]
    events = query_db(
        "SELECT id, user_id, latitude, longitude, message, status, created_at FROM sos_events WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    ) or []

    return jsonify({
        "success": True,
        "events": events
    }), 200
