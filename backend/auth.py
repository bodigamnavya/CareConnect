```python
from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import bcrypt
import jwt
from datetime import datetime, timedelta

# ============================================
# LOAD ENVIRONMENT VARIABLES
# ============================================

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
JWT_SECRET = os.getenv("JWT_SECRET")

if not MONGO_URI:
    raise ValueError("MONGO_URI is not configured")

if not JWT_SECRET:
    raise ValueError("JWT_SECRET is not configured")


# ============================================
# MONGODB CONNECTION
# ============================================

client = MongoClient(MONGO_URI)

db = client["careconnect"]

users_collection = db["users"]


# ============================================
# BLUEPRINT
# ============================================

auth_bp = Blueprint("auth", __name__)


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


        name = str(
            data.get("name", "")
        ).strip()


        email = str(
            data.get("email", "")
        ).strip().lower()


        password = str(
            data.get("password", "")
        )


        # ====================================
        # VALIDATION
        # ====================================

        if not name:

            return jsonify({
                "success": False,
                "message": "Name is required"
            }), 400


        if not email:

            return jsonify({
                "success": False,
                "message": "Email is required"
            }), 400


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


        # ====================================
        # CHECK EXISTING USER
        # ====================================

        existing_user = users_collection.find_one({
            "email": email
        })


        if existing_user:

            return jsonify({
                "success": False,
                "message": "Email already registered"
            }), 409


        # ====================================
        # HASH PASSWORD
        # ====================================

        password_hash = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")


        # ====================================
        # CREATE USER
        # ====================================

        user = {

            "name": name,

            "email": email,

            "password_hash": password_hash,

            "created_at": datetime.utcnow()

        }


        # ====================================
        # SAVE USER
        # ====================================

        result = users_collection.insert_one(user)


        print(
            "USER CREATED:",
            email
        )


        return jsonify({

            "success": True,

            "message": "Registration successful",

            "user": {

                "id": str(
                    result.inserted_id
                ),

                "name": name,

                "email": email

            }

        }), 201


    except Exception as error:

        print(
            "REGISTER ERROR:",
            repr(error)
        )


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

        data = request.get_json(
            silent=True
        )


        if not data:

            return jsonify({
                "success": False,
                "message": "No data received"
            }), 400


        email = str(
            data.get("email", "")
        ).strip().lower()


        password = str(
            data.get("password", "")
        )


        # ====================================
        # VALIDATION
        # ====================================

        if not email:

            return jsonify({
                "success": False,
                "message": "Email is required"
            }), 400


        if not password:

            return jsonify({
                "success": False,
                "message": "Password is required"
            }), 400


        # ====================================
        # FIND USER
        # ====================================

        user = users_collection.find_one({
            "email": email
        })


        if not user:

            return jsonify({

                "success": False,

                "message":
                    "Invalid email or password"

            }), 401


        # ====================================
        # CHECK PASSWORD
        # ====================================

        password_match = bcrypt.checkpw(

            password.encode("utf-8"),

            user["password_hash"].encode("utf-8")

        )


        if not password_match:

            return jsonify({

                "success": False,

                "message":
                    "Invalid email or password"

            }), 401


        # ====================================
        # CREATE JWT TOKEN
        # ====================================

        token = jwt.encode(

            {

                "user_id":
                    str(user["_id"]),

                "email":
                    user["email"],

                "exp":
                    datetime.utcnow()
                    + timedelta(hours=24)

            },

            JWT_SECRET,

            algorithm="HS256"

        )


        # ====================================
        # LOGIN SUCCESS
        # ====================================

        return jsonify({

            "success": True,

            "message":
                "Login successful",

            "token":
                token,

            "user": {

                "id":
                    str(user["_id"]),

                "name":
                    user["name"],

                "email":
                    user["email"]

            }

        }), 200


    except Exception as error:

        print(
            "LOGIN ERROR:",
            repr(error)
        )


        return jsonify({

            "success": False,

            "message":
                "Login failed",

            "error":
                str(error)

        }), 500


# ============================================
# LOGOUT
# ============================================

@auth_bp.route("/api/logout", methods=["POST"])
def logout():

    return jsonify({

        "success": True,

        "message":
            "Logged out successfully"

    }), 200
```
