import uuid
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from utils.security import token_required
from utils.database import query_db, execute_db
from utils.validators import sanitize_string
from utils.mongo import get_health_records_collection

health_records_bp = Blueprint("health_records_bp", __name__)

@health_records_bp.route("/api/health-records", methods=["GET"])
@token_required
def list_health_records(current_user):
    """
    Returns user's saved health records (Allergies, Conditions, Medications, Notes).
    """
    user_id = current_user["id"]
    category = request.args.get("category", "").strip()

    # 1. Try MongoDB
    try:
        col = get_health_records_collection()
        if col is not None:
            q = {"user_id": user_id}
            if category and category.lower() != "all":
                q["category"] = {"$regex": f"^{category}$", "$options": "i"}
            docs = list(col.find(q).sort("created_at", -1))
            if docs:
                records = []
                for d in docs:
                    records.append({
                        "id": str(d.get("id") or d.get("_id")),
                        "user_id": d.get("user_id"),
                        "category": d.get("category"),
                        "title": d.get("title"),
                        "details": d.get("details"),
                        "severity": d.get("severity"),
                        "start_date": d.get("start_date"),
                        "is_active": d.get("is_active", 1),
                        "created_at": d.get("created_at").isoformat() if hasattr(d.get("created_at"), "isoformat") else str(d.get("created_at", ""))
                    })
                return jsonify({
                    "success": True,
                    "records": records
                }), 200
    except Exception as ex:
        print(f"[HealthRecords MongoDB list note]: {ex}")

    # 2. Fallback to SQL
    if category and category.lower() != "all":
        records = query_db(
            "SELECT * FROM health_records WHERE user_id = ? AND LOWER(category) = ? ORDER BY created_at DESC",
            (user_id, category.lower())
        ) or []
    else:
        records = query_db(
            "SELECT * FROM health_records WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        ) or []

    return jsonify({
        "success": True,
        "records": records
    }), 200

@health_records_bp.route("/api/health-records", methods=["POST"])
@token_required
def add_health_record(current_user):
    """
    Creates a new health record entry.
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
    now_iso = datetime.now(timezone.utc).isoformat()

    # 1. Save in MongoDB
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
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            })
    except Exception as ex:
        print(f"[HealthRecords MongoDB save note]: {ex}")

    # 2. Save in SQL
    try:
        execute_db(
            """
            INSERT INTO health_records (id, user_id, category, title, details, severity, start_date, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            """,
            (record_id, user_id, category, title, details, severity, start_date, now_iso, now_iso)
        )
    except Exception:
        pass

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
    Updates an existing health record.
    """
    user_id = current_user["id"]
    data = request.get_json(silent=True) or {}
    category = sanitize_string(data.get("category", "General"))
    title = sanitize_string(data.get("title", ""))
    details = sanitize_string(data.get("details", ""))
    severity = sanitize_string(data.get("severity", "Moderate"))
    start_date = sanitize_string(data.get("start_date", ""))
    is_active = 1 if data.get("is_active", True) else 0
    now_iso = datetime.now(timezone.utc).isoformat()

    if not title:
        return jsonify({"success": False, "message": "Record title is required."}), 400

    # 1. Update in MongoDB
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
                    "updated_at": datetime.now(timezone.utc)
                }}
            )
    except Exception:
        pass

    # 2. Update in SQL
    try:
        execute_db(
            """
            UPDATE health_records
            SET category = ?, title = ?, details = ?, severity = ?, start_date = ?, is_active = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
            """,
            (category, title, details, severity, start_date, is_active, now_iso, record_id, user_id)
        )
    except Exception:
        pass

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
    Deletes a health record.
    """
    user_id = current_user["id"]

    # 1. Delete in MongoDB
    try:
        col = get_health_records_collection()
        if col is not None:
            col.delete_one({"$or": [{"id": record_id}, {"_id": record_id}], "user_id": user_id})
    except Exception:
        pass

    # 2. Delete in SQL
    try:
        execute_db("DELETE FROM health_records WHERE id = ? AND user_id = ?", (record_id, user_id))
    except Exception:
        pass

    return jsonify({
        "success": True,
        "message": "Health record removed successfully."
    }), 200
