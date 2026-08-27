from flask import Blueprint, request, jsonify
from utils.security import token_required
from utils.file_security import allowed_file, save_uploaded_file
from utils.validators import sanitize_string
from services.ai_chat import handle_chat_message
from services.symptom_analyzer import analyze_symptoms
from services.triage import evaluate_triage
from services.report_explainer import explain_medical_report, extract_text_from_file
from services.health_summary import generate_patient_health_summary

ai_bp = Blueprint("ai_bp", __name__)

@ai_bp.route("/api/ai/chat", methods=["POST"])
@token_required
def ai_chat(current_user):
    """
    Dedicated AI health chat endpoint with multi-turn context and emergency detection.
    """
    data = request.get_json(silent=True) or {}
    message = sanitize_string(data.get("message", ""))
    conversation_id = sanitize_string(data.get("conversation_id", ""))

    if not message:
        return jsonify({"success": False, "message": "Message cannot be empty."}), 400

    user_id = current_user["id"]
    chat_result = handle_chat_message(user_id, message, conversation_id)
    return jsonify(chat_result), 200

@ai_bp.route("/api/ai/symptoms", methods=["POST"])
@token_required
def symptom_checker(current_user):
    """
    Evaluates symptoms and provides condition categories, self-care, and triage.
    """
    data = request.get_json(silent=True) or {}
    symptoms = data.get("symptoms", [])
    duration = sanitize_string(data.get("duration", ""))
    notes = sanitize_string(data.get("notes", ""))

    if not symptoms:
        return jsonify({"success": False, "message": "Please specify at least one symptom."}), 400

    result = analyze_symptoms(symptoms, duration, notes)
    return jsonify(result), 200

@ai_bp.route("/api/ai/triage", methods=["POST"])
@token_required
def health_triage(current_user):
    """
    Classifies risk into LOW, MODERATE, URGENT.
    """
    data = request.get_json(silent=True) or {}
    symptoms = data.get("symptoms", "")
    duration = sanitize_string(data.get("duration", ""))
    severity = sanitize_string(data.get("severity", "moderate"))

    if not symptoms:
        return jsonify({"success": False, "message": "Symptoms or description required for triage."}), 400

    triage_data = evaluate_triage(symptoms, duration, severity)
    return jsonify({
        "success": True,
        "triage": triage_data
    }), 200

@ai_bp.route("/api/ai/explain-report", methods=["POST"])
@token_required
def explain_report(current_user):
    """
    Parses and explains medical reports/documents or text extracts.
    """
    report_text = ""
    report_type = request.form.get("report_type", "Lab Report").strip()

    # Handle file upload if provided
    if "report_file" in request.files:
        file = request.files["report_file"]
        if file.filename and allowed_file(file.filename, file_type="report"):
            file_path, _ = save_uploaded_file(file, subfolder="reports")
            report_text = extract_text_from_file(file_path)
            
    # Handle direct text input if no file or additional notes
    if not report_text:
        # Check json or form data
        json_data = request.get_json(silent=True) or {}
        report_text = sanitize_string(json_data.get("report_text", "") or request.form.get("report_text", ""))

    if not report_text:
        return jsonify({"success": False, "message": "Please provide report text or upload a medical document."}), 400

    explanation = explain_medical_report(report_text, report_type)
    return jsonify(explanation), 200

@ai_bp.route("/api/ai/health-summary", methods=["POST", "GET"])
@token_required
def health_summary(current_user):
    """
    Generates personalized health summary grounded in user's saved data.
    """
    user_id = current_user["id"]
    summary_data = generate_patient_health_summary(user_id)
    return jsonify(summary_data), 200
