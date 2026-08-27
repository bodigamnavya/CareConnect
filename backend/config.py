import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "CareConnect_Super_Secret_Production_Key_2026")
    JWT_SECRET = os.getenv("JWT_SECRET", "CareConnect_Secure_JWT_2026_Production_Key_987654")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", 48))

    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL")
    # Fix Render postgres:// to postgresql:// if needed
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    # Local fallback sqlite DB path
    SQLITE_PATH = BASE_DIR / "careconnect.sqlite3"

    # AI Configuration
    AI_API_KEY = os.getenv("AI_API_KEY", "")
    AI_MODEL = os.getenv("AI_MODEL", "gemini-1.5-flash")

    # Uploads Configuration
    UPLOAD_FOLDER = BASE_DIR / "uploads"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "pdf"}

    # CORS
    FRONTEND_URL = os.getenv("FRONTEND_URL", "*")
    
    # Disclaimer
    MEDICAL_DISCLAIMER = "This AI result is for preliminary informational assistance only and is not a medical diagnosis. Always consult a qualified healthcare professional for medical concerns."

# Ensure upload directory exists
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
