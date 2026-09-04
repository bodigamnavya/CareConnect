import os
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
from flask import Blueprint, request, jsonify
from pymongo.errors import PyMongoError, DuplicateKeyError
from bson import ObjectId
from dotenv import load_dotenv
from config import Config
from utils.database import get_users_collection

auth_bp = Blueprint("auth_bp", __name__)

# ============================================
# REGISTER
# ============================================
@auth_bp.route("/api/register", methods=["POST"])
def register():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({
                "success": False,
                "message": "No data received"
            }), 400

        name = str(data.get("name", "")).strip()
        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", ""))

        if not name:
            return jsonify({
                "success": False,
                "message": "Full name is required"
            }), 400

        if not email:
            return jsonify({
                "success": False,
                "message": "Email is required"
            }), 400

        if len(password) < 6:
            return jsonify({
                "success": False,
                "message": "Password must contain at least 6 characters"
            }), 400

        users_col = get_users_collection()
        if users_col is None:
            return jsonify({
                "success": False,
                "message": "Database connection failed. Please ensure MONGO_URI is configured."
            }), 500

        existing_user = users_col.find_one({"email": email})
        if existing_user:
            return jsonify({
                "success": False,
                "message": "Email is already registered. Please sign in."
            }), 409

        password_hash = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        user = {
            "name": name,
            "email": email,
            "password_hash": password_hash,
            "created_at": datetime.now(timezone.utc)
        }

        result = users_col.insert_one(user)
        user_id = str(result.inserted_id)

        jwt_key = os.getenv("JWT_SECRET") or Config.JWT_SECRET
        token = jwt.encode(
            {
                "user_id": user_id,
                "email": email,
                "name": name,
                "exp": datetime.now(timezone.utc) + timedelta(hours=Config.JWT_EXPIRATION_HOURS)
            },
            jwt_key,
            algorithm="HS256"
        )

        return jsonify({
            "success": True,
            "message": "Registration successful",
            "token": token,
            "user": {
                "id": user_id,
                "name": name,
                "email": email
            }
        }), 201

    except DuplicateKeyError:
        return jsonify({
            "success": False,
            "message": "Email is already registered. Please sign in."
        }), 409

    except PyMongoError as error:
        print("REGISTER DATABASE ERROR:", repr(error))
        return jsonify({
            "success": False,
            "message": "Database connection failed",
            "error": str(error)
        }), 500

    except Exception as error:
        print("REGISTER ERROR:", repr(error))
        return jsonify({
            "success": False,
            "message": "Registration failed",
            "error": str(error)
        }), 500


# ============================================
# LOGIN
# ============================================
@auth_bp.route("/api/login", methods=["POST"])
def login():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({
                "success": False,
                "message": "No data received"
            }), 400

        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", ""))

        if not email or not password:
            return jsonify({
                "success": False,
                "message": "Email and password are required"
            }), 400

        users_col = get_users_collection()
        if users_col is None:
            return jsonify({
                "success": False,
                "message": "Database connection failed. Please ensure MONGO_URI is configured."
            }), 500

        user = users_col.find_one({"email": email})
        if not user:
            return jsonify({
                "success": False,
                "message": "Invalid email or password"
            }), 401

        stored_hash = user.get("password_hash")
        if not stored_hash:
            return jsonify({
                "success": False,
                "message": "User account data is invalid"
            }), 500

        if isinstance(stored_hash, str):
            stored_hash_bytes = stored_hash.encode("utf-8")
        elif isinstance(stored_hash, bytes):
            stored_hash_bytes = stored_hash
        else:
            stored_hash_bytes = str(stored_hash).encode("utf-8")

        password_match = bcrypt.checkpw(
            password.encode("utf-8"),
            stored_hash_bytes
        )

        if not password_match:
            return jsonify({
                "success": False,
                "message": "Invalid email or password"
            }), 401

        jwt_key = os.getenv("JWT_SECRET") or Config.JWT_SECRET
        user_id = str(user.get("_id") or user.get("id"))
        user_name = user.get("name", "")

        token = jwt.encode(
            {
                "user_id": user_id,
                "email": user["email"],
                "name": user_name,
                "exp": datetime.now(timezone.utc) + timedelta(hours=Config.JWT_EXPIRATION_HOURS)
            },
            jwt_key,
            algorithm="HS256"
        )

        return jsonify({
            "success": True,
            "message": "Login successful",
            "token": token,
            "user": {
                "id": user_id,
                "name": user_name,
                "email": user["email"],
                "phone": user.get("phone", ""),
                "blood_group": user.get("blood_group", "")
            }
        }), 200

    except PyMongoError as error:
        print("LOGIN DATABASE ERROR:", repr(error))
        return jsonify({
            "success": False,
            "message": "Database connection failed",
            "error": str(error)
        }), 500

    except Exception as error:
        print("LOGIN ERROR:", repr(error))
        return jsonify({
            "success": False,
            "message": "Login failed",
            "error": str(error)
        }), 500


# ============================================
# LOGOUT
# ============================================
@auth_bp.route("/api/logout", methods=["POST"])
def logout():
    return jsonify({
        "success": True,
        "message": "Logged out successfully"
    }), 200
