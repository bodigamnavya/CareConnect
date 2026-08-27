from flask import Blueprint, request, jsonify
from utils.security import token_required
from utils.database import query_db

history_bp = Blueprint("history_bp", __name__)

@history_bp.route("/api/history", methods=["GET"])
@token_required
def get_user_history(current_user):
    user_id = current_user["id"]
    scans = query_db("SELECT * FROM scans WHERE user_id = ? ORDER BY created_at DESC", (user_id,)) or []
    return jsonify({
        "success": True,
        "history": scans
    }), 200
