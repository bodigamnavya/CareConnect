import os
import uuid
import json
from datetime import datetime, timezone
from pathlib import Path
from config import Config
from utils.database import query_db, execute_db

def generate_scan_report(user_id: str, scan_id: str) -> dict:
    """
    Generates a formal, formatted clinical scan report document.
    """
    # 1. Fetch user & scan data (MongoDB or SQL)
    user = None
    scan = None

    try:
        from utils.mongo import get_users_collection, get_scans_collection, get_reports_collection
        from bson import ObjectId
        users_col = get_users_collection()
        scans_col = get_scans_collection()
        if users_col is not None:
            try:
                user = users_col.find_one({"_id": ObjectId(user_id)})
            except Exception:
                user = users_col.find_one({"_id": user_id})
        if scans_col is not None:
            scan = scans_col.find_one({"$or": [{"id": scan_id}, {"_id": scan_id}], "user_id": user_id})
    except Exception as ex:
        print(f"[Report Gen MongoDB fetch warning]: {ex}")

    if not user:
        user = query_db("SELECT id, name, email, phone, blood_group FROM users WHERE id = ?", (user_id,), one=True)
    if not scan:
        scan = query_db("SELECT * FROM scans WHERE id = ? AND user_id = ?", (scan_id, user_id), one=True)

    if not user or not scan:
        return {"success": False, "message": "User or scan record not found."}

    report_id = f"rep_{uuid.uuid4().hex[:16]}"
    report_title = f"Health Scan Report - {scan['scan_type']}"
    report_filename = f"report_{scan_id}_{uuid.uuid4().hex[:8]}.html"
    report_dir = Config.UPLOAD_FOLDER / "reports"
    os.makedirs(report_dir, exist_ok=True)
    report_path = report_dir / report_filename


    # 2. Build HTML Document
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>CareConnect Scan Report - {scan['id']}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #1e293b;
            background: #f8fafc;
            padding: 40px;
            margin: 0;
        }}
        .report-card {{
            max-width: 800px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.05);
            padding: 40px;
            border-top: 6px solid #06b6d4;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 20px;
            margin-bottom: 25px;
        }}
        .logo {{
            font-size: 24px;
            font-weight: 800;
            color: #0891b2;
        }}
        .badge {{
            background: #e0f2fe;
            color: #0369a1;
            padding: 6px 14px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 13px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 25px;
            background: #f1f5f9;
            padding: 20px;
            border-radius: 8px;
        }}
        .section-title {{
            font-size: 16px;
            font-weight: 700;
            color: #0f172a;
            border-left: 4px solid #06b6d4;
            padding-left: 10px;
            margin: 25px 0 10px 0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .result-box {{
            background: #f0fdfa;
            border: 1px solid #99f6e4;
            padding: 18px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .result-text {{
            font-size: 18px;
            font-weight: 700;
            color: #0f766e;
        }}
        .confidence {{
            font-weight: 600;
            color: #0d9488;
        }}
        .disclaimer-box {{
            margin-top: 35px;
            padding: 16px;
            background: #fef2f2;
            border-left: 4px solid #ef4444;
            border-radius: 6px;
            font-size: 12px;
            color: #991b1b;
        }}
        .footer {{
            margin-top: 30px;
            text-align: center;
            font-size: 12px;
            color: #64748b;
        }}
        @media print {{
            body {{ background: #fff; padding: 0; }}
            .report-card {{ box-shadow: none; padding: 20px; border: none; }}
        }}
    </style>
</head>
<body>
    <div class="report-card">
        <div class="header">
            <div class="logo">🚑 CARECONNECT HEALTHCARE</div>
            <div class="badge">AI PRELIMINARY SCAN REPORT</div>
        </div>

        <div class="grid">
            <div>
                <strong>Patient Name:</strong> {user['name']}<br>
                <strong>Email:</strong> {user['email']}<br>
                <strong>Blood Group:</strong> {user.get('blood_group') or 'N/A'}
            </div>
            <div>
                <strong>Scan ID:</strong> {scan['id']}<br>
                <strong>Scan Date:</strong> {scan['created_at']}<br>
                <strong>Scan Type:</strong> {scan['scan_type']}
            </div>
        </div>

        <div class="section-title">AI Analysis & Detected Result</div>
        <div class="result-box">
            <div class="result-text">{scan['result']}</div>
            <div class="confidence">Confidence Score: {scan['confidence']}%</div>
        </div>

        <div class="section-title">Detailed Explanation</div>
        <p>{scan['explanation']}</p>

        <div class="section-title">Possible Meaning & Clinical Indications</div>
        <p>{scan['possible_meaning']}</p>

        <div class="section-title">Recommended Next Steps & Guidance</div>
        <p>{scan['recommendation']}</p>

        <div class="section-title">Warning Signs & When to Seek In-Person Care</div>
        <p>{scan['warning_signs']}</p>

        <div class="disclaimer-box">
            <strong>IMPORTANT MEDICAL NOTICE:</strong><br>
            {Config.MEDICAL_DISCLAIMER}
        </div>

        <div class="footer">
            Generated securely by CareConnect AI Platform • Patient Copy • {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}
        </div>
    </div>
</body>
</html>
"""
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # 3. Store in reports (MongoDB & SQL)
    rel_file_url = f"/uploads/reports/{report_filename}"
    content_json = {
        "scan_id": scan["id"],
        "scan_type": scan["scan_type"],
        "result": scan["result"],
        "confidence": scan["confidence"]
    }
    now_iso = datetime.now(timezone.utc).isoformat()

    try:
        from utils.mongo import get_reports_collection
        rep_col = get_reports_collection()
        if rep_col is not None:
            rep_col.insert_one({
                "_id": report_id,
                "id": report_id,
                "user_id": user_id,
                "scan_id": scan["id"],
                "report_type": "SCAN_REPORT",
                "title": report_title,
                "file_path": rel_file_url,
                "content_json": content_json,
                "summary_text": scan["explanation"][:200],
                "created_at": datetime.now(timezone.utc)
            })
    except Exception as ex:
        print(f"[Report Gen MongoDB save warning]: {ex}")

    try:
        execute_db(
            "INSERT INTO reports (id, user_id, scan_id, report_type, title, file_path, content_json, summary_text, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                report_id,
                user_id,
                scan["id"],
                "SCAN_REPORT",
                report_title,
                rel_file_url,
                json.dumps(content_json),
                scan["explanation"][:200],
                now_iso
            )
        )
    except Exception:
        pass


    return {
        "success": True,
        "report_id": report_id,
        "title": report_title,
        "download_url": rel_file_url,
        "message": "Report generated successfully."
    }
