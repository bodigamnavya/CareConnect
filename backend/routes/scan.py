from flask import Blueprint, request, jsonify
from utils.security import token_required
from utils.file_security import allowed_file
from utils.database import query_db, execute_db
from services.scanner import process_and_save_scan

scan_bp = Blueprint("scan_bp", __name__)

@scan_bp.route("/api/scan", methods=["POST"])
@token_required
def perform_scan(current_user):
    """
    Handles medical image scan upload, validation, AI analysis, and saving.
    """
    if "image" not in request.files:
        return jsonify({"success": False, "message": "Please select or capture a medical image to scan."}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"success": False, "message": "No image file selected."}), 400

    if not allowed_file(file.filename, file_type="image"):
        return jsonify({"success": False, "message": "Unsupported file format. Please upload PNG, JPG, JPEG, or WEBP."}), 400

    scan_type = request.form.get("scan_type", "General Medical Scan").strip()
    user_id = current_user["id"]

    try:
        scan_response = process_and_save_scan(user_id, file, scan_type)
        return jsonify(scan_response), 201
    except Exception as e:
        print(f"[Scan Route Error]: {e}")
        return jsonify({
            "success": False,
            "message": "An error occurred while analyzing the medical image. Please try again."
        }), 500

@scan_bp.route("/api/scans", methods=["GET"])
@token_required
def list_scans(current_user):
    """
    Returns user-specific scan history with optional search/filter.
    """
    user_id = current_user["id"]
    scan_type = request.args.get("type", "").strip()
    search = request.args.get("search", "").strip().lower()

    # 1. Try MongoDB
    try:
        from utils.mongo import get_scans_collection
        scans_col = get_scans_collection()
        if scans_col is not None:
            query = {"user_id": user_id}
            if scan_type and scan_type.lower() != "all":
                query["scan_type"] = {"$regex": f"^{scan_type}$", "$options": "i"}
            
            mongo_scans = list(scans_col.find(query).sort("created_at", -1))
            if mongo_scans:
                results = []
                for s in mongo_scans:
                    item = {
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
                    }
                    if search:
                        if search not in item["result"].lower() and search not in item["explanation"].lower():
                            continue
                    results.append(item)
                return jsonify({
                    "success": True,
                    "count": len(results),
                    "scans": results
                }), 200
    except Exception as ex:
        print(f"[Scan MongoDB list warning]: {ex}")

    # 2. Fallback to SQL
    query = "SELECT * FROM scans WHERE user_id = ?"
    params = [user_id]

    if scan_type and scan_type.lower() != "all":
        query += " AND LOWER(scan_type) = ?"
        params.append(scan_type.lower())

    if search:
        query += " AND (LOWER(result) LIKE ? OR LOWER(explanation) LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    query += " ORDER BY created_at DESC"

    scans = query_db(query, tuple(params)) or []

    return jsonify({
        "success": True,
        "count": len(scans),
        "scans": scans
    }), 200

@scan_bp.route("/api/scans/<scan_id>", methods=["GET"])
@token_required
def get_scan(current_user, scan_id):
    """
    Fetch single scan details.
    """
    user_id = current_user["id"]

    # 1. Try MongoDB
    try:
        from utils.mongo import get_scans_collection
        scans_col = get_scans_collection()
        if scans_col is not None:
            s = scans_col.find_one({"$or": [{"id": scan_id}, {"_id": scan_id}], "user_id": user_id})
            if s:
                return jsonify({
                    "success": True,
                    "scan": {
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
                    }
                }), 200
    except Exception:
        pass

    # 2. Fallback to SQL
    scan = query_db("SELECT * FROM scans WHERE id = ? AND user_id = ?", (scan_id, user_id), one=True)
    if not scan:
        return jsonify({"success": False, "message": "Scan not found or access denied."}), 404

    return jsonify({
        "success": True,
        "scan": scan
    }), 200

@scan_bp.route("/api/scans/<scan_id>", methods=["DELETE"])
@token_required
def delete_scan(current_user, scan_id):
    """
    Delete a scan record safely.
    """
    user_id = current_user["id"]

    # 1. Delete in MongoDB
    try:
        from utils.mongo import get_scans_collection
        scans_col = get_scans_collection()
        if scans_col is not None:
            scans_col.delete_one({"$or": [{"id": scan_id}, {"_id": scan_id}], "user_id": user_id})
    except Exception:
        pass

    # 2. Delete in SQL
    try:
        execute_db("DELETE FROM scans WHERE id = ? AND user_id = ?", (scan_id, user_id))
    except Exception:
        pass

    return jsonify({
        "success": True,
        "message": "Scan record deleted successfully."
    }), 200

