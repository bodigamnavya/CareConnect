from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
import jwt
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
JWT_SECRET = os.getenv("JWT_SECRET")

if not MONGO_URI:
    raise ValueError("MONGO_URI is not configured")

if not JWT_SECRET:
    raise ValueError("JWT_SECRET is not configured")

client = MongoClient(MONGO_URI)

db = client["careconnect"]
medical_collection = db["medical_profiles"]

medical = Blueprint("medical", __name__)


def get_user_from_token():

    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return None

    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ", 1)[1]

    try:

        decoded = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=["HS256"]
        )

        return decoded

    except jwt.ExpiredSignatureError:

        return None

    except jwt.InvalidTokenError:

        return None


@medical.route("/api/medical-profile", methods=["POST"])
def save_medical_profile():

    user = get_user_from_token()

    if not user:
        return jsonify({
            "success": False,
            "message": "Unauthorized. Please login again."
        }), 401

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "No data received"
        }), 400

    blood_group = data.get("blood_group", "").strip()
    phone = data.get("phone", "").strip()
    allergies = data.get("allergies", "").strip()
    medications = data.get("medications", "").strip()
    conditions = data.get("conditions", "").strip()
    emergency_contact = data.get(
        "emergency_contact", ""
    ).strip()

    if not blood_group:

        return jsonify({
            "success": False,
            "message": "Blood group is required"
        }), 400

    if not phone:

        return jsonify({
            "success": False,
            "message": "Emergency phone is required"
        }), 400

    if not emergency_contact:

        return jsonify({
            "success": False,
            "message": "Emergency contact is required"
        }), 400

    user_id = user["user_id"]

    medical_data = {
        "user_id": user_id,
        "blood_group": blood_group,
        "phone": phone,
        "allergies": allergies,
        "medications": medications,
        "conditions": conditions,
        "emergency_contact": emergency_contact
    }

    # Debug information
    print("MEDICAL DATA:", medical_data)

    # Save or update medical profile
    result = medical_collection.update_one(
        {"user_id": user_id},
        {"$set": medical_data},
        upsert=True
    )

    print(
        "MONGODB RESULT:",
        "upserted_id =", result.upserted_id,
        "modified_count =", result.modified_count
    )

    return jsonify({
        "success": True,
        "message": "Medical profile saved successfully"
    }), 200