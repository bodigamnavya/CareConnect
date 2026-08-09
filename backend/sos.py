from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import jwt
from datetime import datetime, timezone

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
JWT_SECRET = os.getenv("JWT_SECRET")

client = MongoClient(MONGO_URI)
db = client["careconnect"]

sos_events_collection = db["sos_events"]

sos = Blueprint("sos", __name__)


def get_user_from_token():

    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return None

    try:
        parts = auth_header.split(" ")

        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        token = parts[1]

        decoded = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=["HS256"]
        )

        return decoded

    except Exception:
        return None


@sos.route("/api/sos", methods=["POST"])
def create_sos():

    user = get_user_from_token()

    if not user:
        return jsonify({
            "success": False,
            "message": "Unauthorized. Please login first."
        }), 401

    data = request.get_json() or {}

    latitude = data.get("latitude")
    longitude = data.get("longitude")
    message = data.get(
        "message",
        "Emergency! I need medical assistance."
    )

    sos_event = {
        "user_id": user["user_id"],
        "latitude": latitude,
        "longitude": longitude,
        "message": message,
        "status": "ACTIVE",
        "created_at": datetime.now(timezone.utc)
    }

    result = sos_events_collection.insert_one(sos_event)

    return jsonify({
        "success": True,
        "message": "Emergency SOS activated",
        "sos_id": str(result.inserted_id),
        "status": "ACTIVE"
    }), 201


@sos.route("/api/sos/history", methods=["GET"])
def sos_history():

    user = get_user_from_token()

    if not user:
        return jsonify({
            "success": False,
            "message": "Unauthorized. Please login first."
        }), 401

    events = list(
        sos_events_collection.find(
            {"user_id": user["user_id"]}
        ).sort("created_at", -1)
    )

    for event in events:
        event["_id"] = str(event["_id"])

    return jsonify({
        "success": True,
        "events": events
    })