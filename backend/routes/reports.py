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
