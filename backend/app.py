from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv
import os

from auth import auth
from medical import medical
from sos import sos
from qr import qr

load_dotenv()

app = Flask(__name__)

CORS(app)
app.register_blueprint(auth)
app.register_blueprint(medical)
app.register_blueprint(sos)
app.register_blueprint(qr)

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)

db = client["careconnect"]

users_collection = db["users"]
medical_profiles_collection = db["medical_profiles"]
emergency_contacts_collection = db["emergency_contacts"]
qr_tokens_collection = db["qr_tokens"]
sos_events_collection = db["sos_events"]
access_logs_collection = db["access_logs"]


@app.route("/")
def home():
    return jsonify({
        "success": True,
        "message": "CareConnect API is running 🚑"
    })


@app.route("/api/health")
def health():
    try:
        client.admin.command("ping")

        return jsonify({
            "success": True,
            "status": "healthy",
            "database": "MongoDB connected",
            "application": "CareConnect"
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "status": "unhealthy",
            "database": "MongoDB connection failed",
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )