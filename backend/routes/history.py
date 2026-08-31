from flask import Blueprint, request, jsonify
from utils.security import token_required
from utils.database import query_db

history_bp = Blueprint("history_bp", __name__)

@history_bp.route("/api/history", methods=["GET"])
@token_required
def get_user_history(current_user):
    user_id = current_user["id"]
    
    # 1. Check MongoDB
    try:
        from utils.mongo import get_scans_collection
        scans_col = get_scans_collection()
        if scans_col is not None:
            mongo_scans = list(scans_col.find({"user_id": user_id}).sort("created_at", -1))
            if mongo_scans:
                results = []
                for s in mongo_scans:
                    results.append({
                        "id": str(s.get("id") or s.get("_id")),
                        "user_id": s.get("user_id"),
                        "scan_type": s.get("scan_type"),
                        "image_path": s.get("image_path"),
                        "image_url": s.get("image_url"),
                        "result": s.get("result"),
                        "confidence": s.get("confidence"),
                        "explanation": s.get("explanation"),
                        "possible_meaning": s.get("possible_meaning"),
                        "recommendation": s.get("recommendation"),
                        "warning_signs": s.get("warning_signs"),
                        "disclaimer": s.get("disclaimer"),
                        "status": s.get("status", "COMPLETED"),
                        "created_at": s.get("created_at").isoformat() if hasattr(s.get("created_at"), "isoformat") else str(s.get("created_at", ""))
                    })
                return jsonify({
                    "success": True,
                    "history": results
                }), 200
    except Exception as ex:
        print(f"[History MongoDB fetch note]: {ex}")

    # 2. Fallback to SQL
    scans = query_db("SELECT * FROM scans WHERE user_id = ? ORDER BY created_at DESC", (user_id,)) or []
    return jsonify({
        "success": True,
        "history": scans
    }), 200

