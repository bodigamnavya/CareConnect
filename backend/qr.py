from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import jwt
import uuid
import qrcode
import base64
from io import BytesIO
from datetime import datetime, timezone

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
JWT_SECRET = os.getenv("JWT_SECRET")

if not MONGO_URI:
    raise ValueError("MONGO_URI is not configured")

if not JWT_SECRET:
    raise ValueError("JWT_SECRET is not configured")

client = MongoClient(MONGO_URI)

db = client["careconnect"]

medical_profiles_collection = db["medical_profiles"]
qr_tokens_collection = db["qr_tokens"]
access_logs_collection = db["access_logs"]

qr = Blueprint("qr", __name__)


# ==========================================
# GET USER FROM JWT TOKEN
# ==========================================

def get_user_from_token():

    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return None

    try:

        parts = auth_header.split(" ")

        if len(parts) != 2:
            return None

        if parts[0].lower() != "bearer":
            return None

        token = parts[1]

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

    except Exception:

        return None


# ==========================================
# GENERATE MEDICAL QR
# ==========================================

@qr.route("/api/generate-qr", methods=["GET"])
def generate_qr():

    user = get_user_from_token()

    if not user:

        return jsonify({
            "success": False,
            "message": "Unauthorized. Please login first."
        }), 401

    user_id = user["user_id"]

    profile = medical_profiles_collection.find_one({
        "user_id": user_id
    })

    if not profile:

        return jsonify({
            "success": False,
            "message": "Medical profile not found. Please save your medical profile first."
        }), 404

    # Generate unique QR token
    qr_token = uuid.uuid4().hex

    qr_document = {
        "token": qr_token,
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc),
        "active": True
    }

    qr_tokens_collection.insert_one(qr_document)

    # URL stored inside QR
    scan_url = (
        "http://192.168.1.9:5000/api/qr/view/"
        + qr_token
    )

    # Generate QR image
    qr_image = qrcode.make(scan_url)

    image_buffer = BytesIO()

    qr_image.save(
        image_buffer,
        format="PNG"
    )

    image_buffer.seek(0)

    # Convert QR image to Base64
    qr_base64 = base64.b64encode(
        image_buffer.getvalue()
    ).decode("utf-8")

    return jsonify({
        "success": True,
        "message": "QR generated successfully.",
        "qr_code": qr_base64
    }), 200


# ==========================================
# VIEW MEDICAL INFORMATION THROUGH QR
# ==========================================

@qr.route("/api/qr/view/<token>", methods=["GET"])
def view_qr(token):

    qr_document = qr_tokens_collection.find_one({
        "token": token,
        "active": True
    })

    if not qr_document:

        return jsonify({
            "success": False,
            "message": "Invalid or inactive QR code"
        }), 404

    user_id = qr_document["user_id"]

    profile = medical_profiles_collection.find_one({
        "user_id": user_id
    })

    if not profile:

        return jsonify({
            "success": False,
            "message": "Medical profile not found"
        }), 404

    # Log QR access
    access_logs_collection.insert_one({
        "user_id": user_id,
        "access_type": "QR_SCAN",
        "accessed_at": datetime.now(timezone.utc)
    })

    # Remove MongoDB internal ID
    profile.pop("_id", None)

    return jsonify({
        "success": True,
        "message": "Emergency medical information",
        "medical_profile": profile
    }), 200