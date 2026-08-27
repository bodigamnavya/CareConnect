from config import Config
from utils.database import query_db

def generate_patient_health_summary(user_id: str) -> dict:
    """
    Combines user's stored information (scans, health records, reports, recent activity)
    and generates an accurate, evidence-grounded clinical health summary.
    """
    # 1. Fetch user information
    user = query_db("SELECT id, name, email, blood_group, emergency_contact, emergency_phone FROM users WHERE id = ?", (user_id,), one=True)
    if not user:
        return {"success": False, "message": "User not found."}

    # 2. Fetch scans
    scans = query_db("SELECT id, scan_type, result, confidence, created_at FROM scans WHERE user_id = ? ORDER BY created_at DESC", (user_id,)) or []
    
    # 3. Fetch health records
    records = query_db("SELECT id, category, title, details, severity, is_active FROM health_records WHERE user_id = ?", (user_id,)) or []

    # 4. Fetch reports
    reports = query_db("SELECT id, title, report_type, created_at FROM reports WHERE user_id = ?", (user_id,)) or []

    total_scans = len(scans)
    total_records = len(records)
    total_reports = len(reports)

    # Categorize records
    allergies = [r["title"] for r in records if r["category"].lower() == "allergy"]
    conditions = [r["title"] for r in records if r["category"].lower() == "condition"]
    medications = [r["title"] for r in records if r["category"].lower() == "medication"]

    # Build grounded summary paragraph
    summary_paragraph = (
        f"Health profile for {user['name']}. Your CareConnect activity reflects {total_scans} medical scan(s), "
        f"{total_records} recorded health item(s), and {total_reports} clinical report(s). "
    )

    if total_scans > 0:
        latest_scan = scans[0]
        summary_paragraph += f"Your most recent scan was a {latest_scan['scan_type']} with detected result: '{latest_scan['result']}' ({latest_scan['confidence']}% confidence). "
    else:
        summary_paragraph += "No medical scans have been completed yet. "

    if allergies:
        summary_paragraph += f"Active recorded allergies include: {', '.join(allergies)}. "
    if conditions:
        summary_paragraph += f"Tracked conditions include: {', '.join(conditions)}. "
    if medications:
        summary_paragraph += f"Current medications noted: {', '.join(medications)}. "

    # Structured guidance recommendations
    guidance = [
        "Continue keeping your allergy and medication lists updated before clinical visits.",
        "Maintain routine annual preventative check-ups and wellness screenings with your doctor.",
        "Store digital copies of any new lab work or diagnostic imaging in CareConnect for continuous record tracking."
    ]

    return {
        "success": True,
        "patient_name": user["name"],
        "blood_group": user.get("blood_group") or "Not specified",
        "emergency_contact": user.get("emergency_contact") or "Not specified",
        "total_scans": total_scans,
        "total_records": total_records,
        "total_reports": total_reports,
        "allergies": allergies,
        "conditions": conditions,
        "medications": medications,
        "summary_text": summary_paragraph,
        "guidance": guidance,
        "disclaimer": Config.MEDICAL_DISCLAIMER
    }
