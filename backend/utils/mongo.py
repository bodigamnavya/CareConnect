import os
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient
from pymongo.errors import PyMongoError, DuplicateKeyError
from bson import ObjectId
from config import Config

_client = None
_db = None
_collections = {}
_indexes_initialized = False

def get_mongo_client():
    """Returns a singleton MongoClient instance or None if not configured."""
    global _client
    mongo_uri = os.getenv("MONGO_URI") or getattr(Config, "MONGO_URI", "")
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
            print(f"[MongoDB] Connection initialization warning: {e}")
            return None
    return _client

def get_mongo_db():
    """Returns the careconnect MongoDB database instance or None."""
    global _db
    client = get_mongo_client()
    if client is not None:
        if _db is None:
            db_name = os.getenv("MONGO_DB_NAME") or getattr(Config, "MONGO_DB_NAME", "careconnect")
            _db = client[db_name]
        return _db
    return None

def get_collection(collection_name: str):
    """Returns requested MongoDB collection with index initialization."""
    global _indexes_initialized
    db = get_mongo_db()
    if db is None:
        return None
    if collection_name not in _collections:
        _collections[collection_name] = db[collection_name]
        if collection_name == "users" and not _indexes_initialized:
            try:
                _collections["users"].create_index("email", unique=True)
                _indexes_initialized = True
            except Exception as e:
                print(f"[MongoDB] Index creation note: {e}")
    return _collections[collection_name]

# Helper accessors
def get_users_collection():
    return get_collection("users")

def get_medical_profiles_collection():
    return get_collection("medical_profiles")

def get_qr_tokens_collection():
    return get_collection("qr_tokens")

def get_access_logs_collection():
    return get_collection("access_logs")

def get_sos_events_collection():
    return get_collection("sos_events")

def get_scans_collection():
    return get_collection("scans")

def get_reports_collection():
    return get_collection("reports")

def get_health_records_collection():
    return get_collection("health_records")
