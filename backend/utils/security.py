import bcrypt
import jwt
from functools import wraps
from datetime import datetime, timezone, timedelta
from flask import request, jsonify
from config import Config
from utils.database import query_db

def hash_password(password: str) -> str:
    """Hash plain text password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def check_password(password: str, hashed_password: str) -> bool:
    """Verify password matches bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def generate_jwt(user_id: str, email: str) -> str:
    """Generate signed JWT token."""
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=Config.JWT_EXPIRATION_HOURS),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)

def decode_jwt(token: str):
    """Decode and validate JWT token."""
    try:
        return jwt.decode(token, Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def get_current_user():
    """Extract authenticated user from Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1].strip()
    payload = decode_jwt(token)
    if not payload:
        return None
    user_id = payload.get("user_id") or payload.get("id")
    email = payload.get("email", "")

    # 1. Check MongoDB first if configured
    try:
        from routes.auth import get_users_collection
        from bson import ObjectId
        users_col = get_users_collection()
        if users_col is not None:
            user_doc = None
            if user_id:
                try:
                    user_doc = users_col.find_one({"_id": ObjectId(user_id)})
                except Exception:
                    user_doc = users_col.find_one({"_id": user_id})
            if not user_doc and email:
                user_doc = users_col.find_one({"email": email})
            if user_doc:
                return {
                    "id": str(user_doc.get("_id", user_id)),
                    "name": user_doc.get("name", ""),
                    "email": user_doc.get("email", ""),
                    "phone": user_doc.get("phone", ""),
                    "blood_group": user_doc.get("blood_group", ""),
                    "emergency_contact": user_doc.get("emergency_contact", ""),
                    "emergency_phone": user_doc.get("emergency_phone", "")
                }
    except Exception:
        pass

    # 2. Fallback to SQL database if available
    try:
        user = query_db("SELECT id, name, email, phone, blood_group, emergency_contact, emergency_phone FROM users WHERE id = ?", (user_id,), one=True)
        if user:
            return dict(user)
    except Exception:
        pass

    # 3. Fallback to token payload data if database record not reachable
    if user_id:
        return {
            "id": str(user_id),
            "name": payload.get("name", "User"),
            "email": email,
            "phone": "",
            "blood_group": "",
            "emergency_contact": "",
            "emergency_phone": ""
        }
    return None


def token_required(f):
    """Decorator to require valid JWT token for protected routes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        current_user = get_current_user()
        if not current_user:
            return jsonify({
                "success": False,
                "message": "Unauthorized. Valid authentication token required.",
                "error": "UNAUTHORIZED"
            }), 401
        return f(current_user, *args, **kwargs)
    return decorated
