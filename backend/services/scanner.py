import uuid
from datetime import datetime, timezone
from config import Config
from utils.database import execute_db, query_db
from utils.file_security import save_uploaded_file
from services.ai_model import analyze_image

def process_and_save_scan(user_id: str, file, scan_type: str) -> dict:
    """
    Validates uploaded medical image, executes AI model, and saves record to database.
    """
    file_path, file_url = save_uploaded_file(file, subfolder="scans")
    
    # 1. Execute AI Vision / Clinical Analysis
    ai_result = analyze_image(file_path, scan_type)
    
    # 2. Generate unique scan ID
    scan_id = f"scn_{uuid.uuid4().hex[:16]}"
    now_iso = datetime.now(timezone.utc).isoformat()
    
    # 3. Save to MongoDB if available
    try:
        from utils.mongo import get_scans_collection
        scans_col = get_scans_collection()
        if scans_col is not None:
            scans_col.insert_one({
                "_id": scan_id,
                "id": scan_id,
                "user_id": user_id,
                "scan_type": scan_type,
                "image_path": file_path,
                "image_url": file_url,
                "result": ai_result["result"],
                "confidence": ai_result["confidence"],
                "explanation": ai_result["explanation"],
                "possible_meaning": ai_result["possible_meaning"],
                "recommendation": ai_result["recommendation"],
                "warning_signs": ai_result["warning_signs"],
                "disclaimer": ai_result["disclaimer"],
                "status": "COMPLETED",
                "created_at": datetime.now(timezone.utc)
            })
    except Exception as ex:
        print(f"[Scanner MongoDB save warning]: {ex}")

    # 4. Save to SQL database if available
    try:
        execute_db(
            """
            INSERT INTO scans (
                id, user_id, scan_type, image_path, image_url,
                result, confidence, explanation, possible_meaning,
                recommendation, warning_signs, disclaimer, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                scan_id, user_id, scan_type, file_path, file_url,
                ai_result["result"], ai_result["confidence"], ai_result["explanation"],
                ai_result["possible_meaning"], ai_result["recommendation"],
                ai_result["warning_signs"], ai_result["disclaimer"], "COMPLETED", now_iso
            )
        )
    except Exception:
        pass


    return {
        "success": True,
        "scan_id": scan_id,
        "scan": {
            "id": scan_id,
            "user_id": user_id,
            "scan_type": scan_type,
            "image_url": file_url,
            "result": ai_result["result"],
            "confidence": ai_result["confidence"],
            "explanation": ai_result["explanation"],
            "possible_meaning": ai_result["possible_meaning"],
            "recommendation": ai_result["recommendation"],
            "warning_signs": ai_result["warning_signs"],
            "disclaimer": ai_result["disclaimer"],
            "status": "COMPLETED",
            "created_at": now_iso
        }
    }
