import os
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from pymongo.errors import PyMongoError, DuplicateKeyError
from bson import ObjectId
from dotenv import load_dotenv
from config import Config

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "")
JWT_SECRET = os.getenv("JWT_SECRET", "CareConnect_Secure_JWT_2026_Production_Key_987654")

# MongoDB connection management
_client = None
_db = None
_users_collection = None
_index_created = False

def get_mongo_client():
    global _client
    mongo_uri = os.getenv("MONGO_URI") or MONGO_URI
    if not mongo_uri:
        return None
    if _client is None:
        try:
            _client = MongoClient(
                mongo_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
        except Exception as e:
            print(f"[MongoDB] Connection error: {e}")
            return None
    return _client

def get_mongo_db():
    global _db
    client = get_mongo_client()
    if client is not None:
        if _db is None:
            _db = client["careconnect"]
        return _db
    return None

def get_users_collection():
    global _users_collection, _index_created
    db = get_mongo_db()
    if db is not None:
        if _users_collection is None:
            _users_collection = db["users"]
            if not _index_created:
                try:
                    _users_collection.create_index("email", unique=True)
                    _index_created = True
                except Exception as e:
                    print(f"[MongoDB] Index creation note: {e}")
        return _users_collection
    return None

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
            # If MongoDB is not configured or unreachable
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
                "exp": datetime.now(timezone.utc) + timedelta(hours=48)
            },
            jwt_key,
            algorithm="HS256"
        )

        return jsonify({
            "success": True,
            "message": "Registration successful! Welcome to CareConnect.",
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

        password_match = bcrypt.checkpw(
            password.encode("utf-8"),
            stored_hash.encode("utf-8")
        )
        if not password_match:
            return jsonify({
                "success": False,
                "message": "Invalid email or password"
            }), 401

        jwt_key = os.getenv("JWT_SECRET") or Config.JWT_SECRET
        token = jwt.encode(
            {
                "user_id": str(user["_id"]),
                "email": user["email"],
                "exp": datetime.now(timezone.utc) + timedelta(hours=48)
            },
            jwt_key,
            algorithm="HS256"
        )

        return jsonify({
            "success": True,
            "message": "Login successful",
            "token": token,
            "user": {
                "id": str(user["_id"]),
                "name": user.get("name", ""),
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

