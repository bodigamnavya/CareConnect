import uuid
from datetime import datetime, timezone
from config import Config
from utils.database import get_scans_collection
from utils.file_security import save_uploaded_file
from services.ai_model import analyze_image

def process_and_save_scan(user_id: str, file, scan_type: str) -> dict:
    """
    Validates uploaded medical image, executes AI model, and saves record to MongoDB.
    """
    file_path, file_url = save_uploaded_file(file, subfolder="scans")
    
    # 1. Execute AI Vision / Clinical Analysis
    ai_result = analyze_image(file_path, scan_type)
    
    # 2. Generate unique scan ID
    scan_id = f"scn_{uuid.uuid4().hex[:16]}"
    now_utc = datetime.now(timezone.utc)
    now_iso = now_utc.isoformat()
    
    # 3. Save to MongoDB
    try:
        scans_col = get_scans_collection()
        if scans_col is not None:
            scans_col.insert_one({
                "_id": scan_id,
                "id": scan_id,
                "user_id": user_id,
                "scan_type": scan_type,
                "image_path": str(file_path),
                "image_url": file_url,
                "result": ai_result["result"],
                "confidence": ai_result["confidence"],
                "explanation": ai_result["explanation"],
                "possible_meaning": ai_result["possible_meaning"],
                "recommendation": ai_result["recommendation"],
                "warning_signs": ai_result["warning_signs"],
                "disclaimer": ai_result["disclaimer"],
                "status": "COMPLETED",
                "created_at": now_utc
            })
    except Exception as ex:
        print(f"[Scanner MongoDB save warning]: {ex}")

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
