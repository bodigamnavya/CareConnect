import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

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

    # MongoDB Configuration
    MONGO_URI = os.getenv("MONGO_URI", "")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "careconnect")

    # Database Configuration (Optional PostgreSQL for Render/Supabase)
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    # SQLite Path configuration: use /tmp on Vercel, local file in BASE_DIR for local development
    if IS_VERCEL:
        SQLITE_PATH = Path(tempfile.gettempdir()) / "careconnect.sqlite3"
    else:
        SQLITE_PATH = BASE_DIR / "careconnect.sqlite3"

    # AI Configuration
    AI_API_KEY = os.getenv("AI_API_KEY", "")
    AI_MODEL = os.getenv("AI_MODEL", "gemini-1.5-flash")

    # Uploads Configuration
    if IS_VERCEL:
        UPLOAD_FOLDER = Path(tempfile.gettempdir()) / "uploads"
    else:
        UPLOAD_FOLDER = BASE_DIR / "uploads"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "pdf"}

    # CORS
    FRONTEND_URL = os.getenv("FRONTEND_URL", "*")
    
    # Disclaimer
    MEDICAL_DISCLAIMER = "This AI result is for preliminary informational assistance only and is not a medical diagnosis. Always consult a qualified healthcare professional for medical concerns."

# Ensure upload and local storage directories exist safely
try:
    if not IS_VERCEL:
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        if Config.SQLITE_PATH.parent:
            os.makedirs(Config.SQLITE_PATH.parent, exist_ok=True)
    else:
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
except Exception:
    pass

