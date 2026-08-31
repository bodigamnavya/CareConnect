import uuid
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from utils.security import token_required
from utils.database import get_health_records_collection
from utils.validators import sanitize_string

health_records_bp = Blueprint("health_records_bp", __name__)

@health_records_bp.route("/api/health-records", methods=["GET"])
@token_required
def list_health_records(current_user):
    """
    Returns user's saved health records (Allergies, Conditions, Medications, Notes) from MongoDB.
    """
    user_id = current_user["id"]
    category = request.args.get("category", "").strip()
    records = []

    try:
        col = get_health_records_collection()
        if col is not None:
            q = {"user_id": user_id}
            if category and category.lower() != "all":
                q["category"] = {"$regex": f"^{category}$", "$options": "i"}
            docs = list(col.find(q).sort("created_at", -1))
            for d in docs:
                records.append({
                    "id": str(d.get("id") or d.get("_id")),
                    "user_id": d.get("user_id"),
                    "category": d.get("category", "General"),
                    "title": d.get("title", ""),
                    "details": d.get("details", ""),
                    "severity": d.get("severity", "Moderate"),
                    "start_date": d.get("start_date", ""),
                    "is_active": d.get("is_active", 1),
                    "created_at": d.get("created_at").isoformat() if hasattr(d.get("created_at"), "isoformat") else str(d.get("created_at", ""))
                })
    except Exception as ex:
        print(f"[HealthRecords MongoDB list note]: {ex}")

    return jsonify({
        "success": True,
        "records": records
    }), 200

@health_records_bp.route("/api/health-records", methods=["POST"])
@token_required
def add_health_record(current_user):
    """
    Creates a new health record entry in MongoDB.
    """
    data = request.get_json(silent=True) or {}
    category = sanitize_string(data.get("category", "General"))
    title = sanitize_string(data.get("title", ""))
    details = sanitize_string(data.get("details", ""))
    severity = sanitize_string(data.get("severity", "Moderate"))
    start_date = sanitize_string(data.get("start_date", ""))

    if not title:
        return jsonify({"success": False, "message": "Record title is required."}), 400

    user_id = current_user["id"]
    record_id = f"rec_{uuid.uuid4().hex[:16]}"
    now_utc = datetime.now(timezone.utc)
    now_iso = now_utc.isoformat()

    try:
        col = get_health_records_collection()
        if col is not None:
            col.insert_one({
                "_id": record_id,
                "id": record_id,
                "user_id": user_id,
                "category": category,
                "title": title,
                "details": details,
                "severity": severity,
                "start_date": start_date,
                "is_active": 1,
                "created_at": now_utc,
                "updated_at": now_utc
            })
    except Exception as ex:
        print(f"[HealthRecords MongoDB save note]: {ex}")

    new_rec = {
        "id": record_id,
        "user_id": user_id,
        "category": category,
        "title": title,
        "details": details,
        "severity": severity,
        "start_date": start_date,
        "is_active": 1,
        "created_at": now_iso
    }

    return jsonify({
        "success": True,
        "message": "Health record added successfully.",
        "record": new_rec
    }), 201

@health_records_bp.route("/api/health-records/<record_id>", methods=["PUT"])
@token_required
def update_health_record(current_user, record_id):
    """
    Updates an existing health record in MongoDB.
    """
    user_id = current_user["id"]
    data = request.get_json(silent=True) or {}
    category = sanitize_string(data.get("category", "General"))
    title = sanitize_string(data.get("title", ""))
    details = sanitize_string(data.get("details", ""))
    severity = sanitize_string(data.get("severity", "Moderate"))
    start_date = sanitize_string(data.get("start_date", ""))
    is_active = 1 if data.get("is_active", True) else 0
    now_utc = datetime.now(timezone.utc)
    now_iso = now_utc.isoformat()

    if not title:
        return jsonify({"success": False, "message": "Record title is required."}), 400

    try:
        col = get_health_records_collection()
        if col is not None:
            col.update_one(
                {"$or": [{"id": record_id}, {"_id": record_id}], "user_id": user_id},
                {"$set": {
                    "category": category,
                    "title": title,
                    "details": details,
                    "severity": severity,
                    "start_date": start_date,
                    "is_active": is_active,
                    "updated_at": now_utc
                }}
            )
    except Exception as ex:
        print(f"[HealthRecords MongoDB update note]: {ex}")

    updated = {
        "id": record_id,
        "user_id": user_id,
        "category": category,
        "title": title,
        "details": details,
        "severity": severity,
        "start_date": start_date,
        "is_active": is_active,
        "updated_at": now_iso
    }

    return jsonify({
        "success": True,
        "message": "Health record updated successfully.",
        "record": updated
    }), 200

@health_records_bp.route("/api/health-records/<record_id>", methods=["DELETE"])
@token_required
def delete_health_record(current_user, record_id):
    """
    Deletes a health record from MongoDB.
    """
    user_id = current_user["id"]

    try:
        col = get_health_records_collection()
        if col is not None:
            col.delete_one({"$or": [{"id": record_id}, {"_id": record_id}], "user_id": user_id})
    except Exception as ex:
        print(f"[HealthRecords MongoDB delete note]: {ex}")

    return jsonify({
        "success": True,
        "message": "Health record removed successfully."
    }), 200
