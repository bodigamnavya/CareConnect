import os
import tempfile
import logging
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
# Load .env from backend directory or parent directory
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")

# Comprehensive detection of Vercel and serverless execution environments
IS_VERCEL = bool(
    os.getenv("VERCEL")
    or os.getenv("VERCEL_ENV")
    or os.getenv("VERCEL_REGION")
    or os.getenv("NOW_REGION")
    or os.getenv("AWS_LAMBDA_FUNCTION_NAME")
    or os.getenv("LAMBDA_TASK_ROOT")
    or str(BASE_DIR).startswith("/var/task")
)


def _safe_int(value, default):
    try:
        if value and str(value).strip():
            return int(value)
    except (ValueError, TypeError):
        pass
    return default


def _safe_float(value, default):
    try:
        if value and str(value).strip():
            return float(value)
    except (ValueError, TypeError):
        pass
    return default


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY") or "CareConnect_Super_Secret_Production_Key_2026"
    JWT_SECRET = os.getenv("JWT_SECRET") or "CareConnect_Secure_JWT_2026_Production_Key_987654"
    JWT_ALGORITHM = "HS256"
    
    _jwt_hours = os.getenv("JWT_EXPIRATION_HOURS")
    JWT_EXPIRATION_HOURS = _safe_int(_jwt_hours, 48)

    # MongoDB Configuration (Primary & Only Persistent Database)
    MONGO_URI = os.getenv("MONGO_URI") or ""
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME") or "careconnect"

    # AI Configuration
    AI_API_KEY = os.getenv("AI_API_KEY") or ""
    AI_MODEL = os.getenv("AI_MODEL") or "gemini-1.5-flash"

    # Uploads Configuration (Ephemeral in serverless, local disk in dev)
    if IS_VERCEL or os.getenv("VERCEL") or not os.access(str(BASE_DIR), os.W_OK):
        UPLOAD_FOLDER = Path(tempfile.gettempdir()) / "uploads"
    else:
        UPLOAD_FOLDER = BASE_DIR / "uploads"

    _max_content_len = os.getenv("MAX_CONTENT_LENGTH")
    MAX_CONTENT_LENGTH = _safe_int(_max_content_len, 16 * 1024 * 1024)  # 16 MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "pdf"}

    # CORS
    FRONTEND_URL = os.getenv("FRONTEND_URL") or "*"

    # Clinical Disclaimer
    MEDICAL_DISCLAIMER = "This AI result is for preliminary informational assistance only and is not a medical diagnosis. Always consult a qualified healthcare professional for medical concerns."


# Ensure upload directory exists safely
try:
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
except Exception as e:
    import logging
    logging.error(f"Config loading error: {e}")
    raise
