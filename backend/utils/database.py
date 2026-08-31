import os
from datetime import datetime, timezone
from pymongo import MongoClient
from pymongo.errors import PyMongoError, DuplicateKeyError
from bson import ObjectId
from config import Config

_client = None
_db = None
_collections = {}
_indexes_initialized = False

def get_client():
    """
    Returns a reusable singleton MongoClient instance or None if not configured/unreachable.
    """
    global _client
    mongo_uri = os.getenv("MONGO_URI") or getattr(Config, "MONGO_URI", "")
    if not mongo_uri:
        return None
    if _client is None:
        try:
            _client = MongoClient(
                mongo_uri,
                serverSelectionTimeoutMS=4000,
                connectTimeoutMS=4000,
                socketTimeoutMS=4000
            )
        except Exception as e:
            print(f"[MongoDB] Client initialization error: {e}")
            return None
    return _client

# Alias for backward compatibility
get_mongo_client = get_client

def get_db():
    """
    Returns the careconnect MongoDB database instance or None.
    """
    global _db
    client = get_client()
    if client is not None:
        if _db is None:
            db_name = os.getenv("MONGO_DB_NAME") or getattr(Config, "MONGO_DB_NAME", "careconnect")
            _db = client[db_name]
        return _db
    return None

# Alias for backward compatibility
get_mongo_db = get_db

def get_collection(collection_name: str):
    """
    Returns the requested MongoDB collection or None if database is unavailable.
    """
    db = get_db()
    if db is None:
        return None
    if collection_name not in _collections:
        _collections[collection_name] = db[collection_name]
    return _collections[collection_name]

# Helper collection accessors
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

def get_ambulance_requests_collection():
    return get_collection("ambulance_requests")

def get_conversations_collection():
    return get_collection("conversations")

def get_conversation_messages_collection():
    return get_collection("conversation_messages")

def init_db():
    """
    Ensures essential MongoDB collection indexes exist.
    Does not crash if MongoDB is unreachable during serverless function import.
    """
    global _indexes_initialized
    if _indexes_initialized:
        return True

    try:
        db = get_db()
        if db is None:
            return False

        # Create unique index on email in users collection
        users_col = db["users"]
        users_col.create_index("email", unique=True, background=True)

        # Create index on token in qr_tokens collection
        qr_col = db["qr_tokens"]
        qr_col.create_index("token", unique=True, background=True)

        # Create user_id indexes for fast queries
        db["scans"].create_index("user_id", background=True)
        db["health_records"].create_index("user_id", background=True)
        db["reports"].create_index("user_id", background=True)
        db["medical_profiles"].create_index("user_id", unique=True, background=True)
        db["sos_events"].create_index("user_id", background=True)
        db["ambulance_requests"].create_index("user_id", background=True)
        db["conversations"].create_index("user_id", background=True)
        db["conversation_messages"].create_index("conversation_id", background=True)

        _indexes_initialized = True
        return True
    except Exception as e:
        print(f"[MongoDB] Index setup note: {e}")
        return False

def check_db_connection():
    """
    Performs a safe ping on the MongoDB server.
    Returns (status: bool, message: str, info: dict)
    """
    client = get_client()
    if client is None:
        return False, "MONGO_URI is not configured or client initialization failed", {}
    try:
        client.admin.command("ping")
        db = get_db()
        user_count = 0
        if db is not None:
            try:
                user_count = db["users"].count_documents({})
            except Exception:
                pass
        return True, "MongoDB connected", {"users_count": user_count}
    except Exception as e:
        return False, f"MongoDB ping failed: {str(e)}", {}

# Safe compatibility helpers for any remaining SQL references
def query_db(query, args=(), one=False):
    """
    Legacy compatibility stub. No SQLite operations are executed.
    """
    return None if one else []

def execute_db(query, args=()):
    """
    Legacy compatibility stub. No SQLite operations are executed.
    """
    return 0

def get_db_connection():
    """
    Legacy compatibility stub.
    """
    return None, "mongodb"
