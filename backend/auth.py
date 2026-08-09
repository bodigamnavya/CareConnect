from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import bcrypt
import jwt
from datetime import datetime, timedelta

# Load .env
load_dotenv()

# Environment variables
MONGO_URI = os.getenv("MONGO_URI")
JWT_SECRET = os.getenv("JWT_SECRET")

# Check configuration
if not MONGO_URI:
    raise ValueError("MONGO_URI is not configured")

if not JWT_SECRET:
    raise ValueError("JWT_SECRET is not configured")

# MongoDB connection
client = MongoClient(MONGO_URI)

db = client["careconnect"]
users_collection = db["users"]

# Blueprint
auth = Blueprint("auth", __name__)


# ===============================
# REGISTER
# ===============================

@auth.route("/api/register", methods=["POST"])
def register():

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "No data received"
        }), 400

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    # Validate name
    if not name:
        return jsonify({
            "success": False,
            "message": "Name is required"
        }), 400

    # Validate email
    if not email:
        return jsonify({
            "success": False,
            "message": "Email is required"
        }), 400

    # Validate password
    if not password:
        return jsonify({
            "success": False,
            "message": "Password is required"
        }), 400

    if len(password) < 6:
        return jsonify({
            "success": False,
            "message": "Password must contain at least 6 characters"
        }), 400

    # Check existing user
    existing_user = users_collection.find_one({
        "email": email
    })

    if existing_user:
        return jsonify({
            "success": False,
            "message": "Email already registered"
        }), 409

    # Hash password
    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    # Create user
    user = {
        "name": name,
        "email": email,
        "password_hash": password_hash,
        "created_at": datetime.utcnow()
    }

    # Save to MongoDB
    result = users_collection.insert_one(user)

    return jsonify({
        "success": True,
        "message": "Registration successful",
        "user_id": str(result.inserted_id)
    }), 201


# ===============================
# LOGIN
# ===============================

@auth.route("/api/login", methods=["POST"])
def login():

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "No data received"
        }), 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    # Validate email
    if not email:
        return jsonify({
            "success": False,
            "message": "Email is required"
        }), 400

    # Validate password
    if not password:
        return jsonify({
            "success": False,
            "message": "Password is required"
        }), 400

    # Find user
    user = users_collection.find_one({
        "email": email
    })

    if not user:
        return jsonify({
            "success": False,
            "message": "Invalid email or password"
        }), 401

    # Check password
    password_match = bcrypt.checkpw(
        password.encode("utf-8"),
        user["password_hash"].encode("utf-8")
    )

    if not password_match:
        return jsonify({
            "success": False,
            "message": "Invalid email or password"
        }), 401

    # Create JWT token
    token = jwt.encode(
        {
            "user_id": str(user["_id"]),
            "email": user["email"],
            "exp": datetime.utcnow() + timedelta(hours=24)
        },
        JWT_SECRET,
        algorithm="HS256"
    )

    return jsonify({
        "success": True,
        "message": "Login successful",
        "token": token,
        "user": {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"]
        }
    }), 200