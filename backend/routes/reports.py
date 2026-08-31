from flask import Blueprint, request, jsonify, send_file
from utils.security import token_required
from utils.database import query_db
from services.report_generator import generate_scan_report

reports_bp = Blueprint("reports_bp", __name__)

@reports_bp.route("/api/reports/generate", methods=["POST"])
@token_required
def create_report(current_user):
    """
    Triggers generation of a downloadable medical scan report.
    """
    data = request.get_json(silent=True) or {}
    scan_id = data.get("scan_id", "").strip()

    if not scan_id:
        return jsonify({"success": False, "message": "Scan ID is required to generate report."}), 400

    user_id = current_user["id"]
    result = generate_scan_report(user_id, scan_id)
    if not result.get("success"):
        return jsonify(result), 404

    return jsonify(result), 201

@reports_bp.route("/api/reports", methods=["GET"])
@token_required
def list_reports(current_user):
    """
    Lists all generated reports for the current user.
    """
    user_id = current_user["id"]

    # 1. Try MongoDB
    try:
        from utils.mongo import get_reports_collection
        rep_col = get_reports_collection()
        if rep_col is not None:
            mongo_reps = list(rep_col.find({"user_id": user_id}).sort("created_at", -1))
            if mongo_reps:
                reports = []
                for r in mongo_reps:
                    reports.append({
                        "id": str(r.get("id") or r.get("_id")),
                        "user_id": r.get("user_id"),
                        "scan_id": r.get("scan_id"),
                        "report_type": r.get("report_type"),
                        "title": r.get("title"),
                        "file_path": r.get("file_path"),
                        "summary_text": r.get("summary_text"),
                        "created_at": r.get("created_at").isoformat() if hasattr(r.get("created_at"), "isoformat") else str(r.get("created_at", ""))
                    })
                return jsonify({
                    "success": True,
                    "reports": reports
                }), 200
    except Exception as ex:
        print(f"[Reports MongoDB list note]: {ex}")

    # 2. Fallback to SQL
    reports = query_db(
        "SELECT id, user_id, scan_id, report_type, title, file_path, summary_text, created_at FROM reports WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    ) or []

    return jsonify({
        "success": True,
        "reports": reports
    }), 200

@reports_bp.route("/api/reports/<report_id>", methods=["GET"])
@token_required
def get_report_details(current_user, report_id):
    """
    Fetches details of a specific report.
    """
    user_id = current_user["id"]

    # 1. Try MongoDB
    try:
        from utils.mongo import get_reports_collection
        rep_col = get_reports_collection()
        if rep_col is not None:
            r = rep_col.find_one({"$or": [{"id": report_id}, {"_id": report_id}], "user_id": user_id})
            if r:
                return jsonify({
                    "success": True,
                    "report": {
                        "id": str(r.get("id") or r.get("_id")),
                        "user_id": r.get("user_id"),
                        "scan_id": r.get("scan_id"),
                        "report_type": r.get("report_type"),
                        "title": r.get("title"),
                        "file_path": r.get("file_path"),
                        "summary_text": r.get("summary_text"),
                        "content_json": r.get("content_json"),
                        "created_at": r.get("created_at").isoformat() if hasattr(r.get("created_at"), "isoformat") else str(r.get("created_at", ""))
                    }
                }), 200
    except Exception:
        pass

    # 2. Fallback to SQL
    report = query_db(
        "SELECT * FROM reports WHERE id = ? AND user_id = ?",
        (report_id, user_id), one=True
    )
    if not report:
        return jsonify({"success": False, "message": "Report not found."}), 404

    return jsonify({
        "success": True,
        "report": report
    }), 200
