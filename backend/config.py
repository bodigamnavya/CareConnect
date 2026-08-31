import os
import tempfile
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


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "CareConnect_Super_Secret_Production_Key_2026")
    JWT_SECRET = os.getenv("JWT_SECRET", "CareConnect_Secure_JWT_2026_Production_Key_987654")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", 48))

    # MongoDB Configuration (Primary & Only Persistent Database)
    MONGO_URI = os.getenv("MONGO_URI", "")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "careconnect")

    # AI Configuration
    AI_API_KEY = os.getenv("AI_API_KEY", "")
    AI_MODEL = os.getenv("AI_MODEL", "gemini-1.5-flash")

    # Uploads Configuration (Ephemeral in serverless, local disk in dev)
    if IS_VERCEL:
        UPLOAD_FOLDER = Path(tempfile.gettempdir()) / "uploads"
    else:
        UPLOAD_FOLDER = BASE_DIR / "uploads"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "pdf"}

    # CORS
    FRONTEND_URL = os.getenv("FRONTEND_URL", "*")

    # Clinical Disclaimer
    MEDICAL_DISCLAIMER = "This AI result is for preliminary informational assistance only and is not a medical diagnosis. Always consult a qualified healthcare professional for medical concerns."


# Ensure upload directory exists safely
try:
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
except Exception:
    pass
