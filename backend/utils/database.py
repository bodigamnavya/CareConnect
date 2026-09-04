import os
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import PyMongoError, DuplicateKeyError
from config import Config, IS_VERCEL

_client = None
_db = None
_collections = {}
_indexes_initialized = False

# =====================================================================
# LOCAL THREAD-SAFE FALLBACK DATABASE (When MONGO_URI is not set)
# =====================================================================
class LocalCursor:
    def __init__(self, docs):
        self.docs = [dict(d) for d in docs]

    def sort(self, key_or_list, direction=1):
        if isinstance(key_or_list, list):
            for k, d in reversed(key_or_list):
                reverse = (d == -1)
                self.docs.sort(key=lambda x: str(x.get(k, "")), reverse=reverse)
        else:
            reverse = (direction == -1)
            self.docs.sort(key=lambda x: str(x.get(key_or_list, "")), reverse=reverse)
        return self

    def limit(self, n):
        self.docs = self.docs[:n]
        return self

    def skip(self, n):
        self.docs = self.docs[n:]
        return self

    def __iter__(self):
        return iter(self.docs)

    def __len__(self):
        return len(self.docs)


class LocalInsertResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class LocalUpdateResult:
    def __init__(self, matched_count=0, modified_count=0):
        self.matched_count = matched_count
        self.modified_count = modified_count


class LocalCollection:
    def __init__(self, name, db_instance):
        self.name = name
        self.db = db_instance

    def _matches(self, doc, query):
        if not query:
            return True
        for k, v in query.items():
            doc_val = doc.get(k)
            # Handle ObjectId vs string comparison
            if k in ("_id", "id"):
                v_str = str(v)
                doc_id_str = str(doc.get("_id", doc.get("id", "")))
                if doc_id_str != v_str and str(doc.get(k)) != v_str:
                    return False
                continue

            if isinstance(v, dict):
                if "$regex" in v:
                    pattern = v["$regex"]
                    ignore_case = "i" in v.get("$options", "")
                    import re
                    flags = re.IGNORECASE if ignore_case else 0
                    if not re.search(pattern, str(doc_val or ""), flags):
                        return False
                elif "$ne" in v:
                    if doc_val == v["$ne"]:
                        return False
                elif "$in" in v:
                    if doc_val not in v["$in"]:
                        return False
            else:
                if str(doc_val).lower() != str(v).lower() if isinstance(v, str) else doc_val != v:
                    return False
        return True

    def find_one(self, query=None, projection=None):
        docs = self.db._load_collection(self.name)
        for doc in docs:
            if self._matches(doc, query):
                res = dict(doc)
                if "_id" in res and isinstance(res["_id"], str):
                    try:
                        res["_id"] = ObjectId(res["_id"])
                    except Exception:
                        pass
                return res
        return None

    def find(self, query=None, projection=None):
        docs = self.db._load_collection(self.name)
        matched = []
        for doc in docs:
            if self._matches(doc, query):
                res = dict(doc)
                if "_id" in res and isinstance(res["_id"], str):
                    try:
                        res["_id"] = ObjectId(res["_id"])
                    except Exception:
                        pass
                matched.append(res)
        return LocalCursor(matched)

    def insert_one(self, doc):
        docs = self.db._load_collection(self.name)
        new_doc = dict(doc)
        if "_id" not in new_doc:
            new_doc["_id"] = str(ObjectId())
        else:
            new_doc["_id"] = str(new_doc["_id"])

        # Check unique constraints if users
        if self.name == "users" and "email" in new_doc:
            for existing in docs:
                if str(existing.get("email", "")).lower() == str(new_doc.get("email", "")).lower():
                    raise DuplicateKeyError(f"Duplicate email: {new_doc.get('email')}")

        # Serialize datetime
        for k, v in new_doc.items():
            if isinstance(v, datetime):
                new_doc[k] = v.isoformat()

        docs.append(new_doc)
        self.db._save_collection(self.name, docs)
        return LocalInsertResult(ObjectId(new_doc["_id"]) if ObjectId.is_valid(new_doc["_id"]) else new_doc["_id"])

    def update_one(self, query, update, upsert=False):
        docs = self.db._load_collection(self.name)
        matched_idx = -1
        for idx, doc in enumerate(docs):
            if self._matches(doc, query):
                matched_idx = idx
                break

        if matched_idx != -1:
            target = dict(docs[matched_idx])
            if "$set" in update:
                for k, v in update["$set"].items():
                    if isinstance(v, datetime):
                        v = v.isoformat()
                    target[k] = v
            else:
                for k, v in update.items():
                    if not k.startswith("$"):
                        if isinstance(v, datetime):
                            v = v.isoformat()
                        target[k] = v
            docs[matched_idx] = target
            self.db._save_collection(self.name, docs)
            return LocalUpdateResult(matched_count=1, modified_count=1)
        elif upsert:
            new_doc = dict(query)
            if "$set" in update:
                new_doc.update(update["$set"])
            new_doc["_id"] = str(ObjectId())
            docs.append(new_doc)
            self.db._save_collection(self.name, docs)
            return LocalUpdateResult(matched_count=0, modified_count=1)

        return LocalUpdateResult(matched_count=0, modified_count=0)

    def delete_one(self, query):
        docs = self.db._load_collection(self.name)
        for idx, doc in enumerate(docs):
            if self._matches(doc, query):
                docs.pop(idx)
                self.db._save_collection(self.name, docs)
                return True
        return False

    def delete_many(self, query):
        docs = self.db._load_collection(self.name)
        new_docs = [d for d in docs if not self._matches(d, query)]
        self.db._save_collection(self.name, new_docs)
        return True

    def count_documents(self, query=None):
        docs = self.db._load_collection(self.name)
        if not query:
            return len(docs)
        return sum(1 for d in docs if self._matches(d, query))

    def create_index(self, keys, **kwargs):
        return True


class LocalDatabase:
    def __init__(self):
        self._lock = threading.Lock()
        self.db_dir = Path(__file__).resolve().parent.parent / "data"
        self.db_file = self.db_dir / "careconnect_local_db.json"
        try:
            self.db_dir.mkdir(parents=True, exist_ok=True)
            if not self.db_file.exists():
                self.db_file.write_text("{}", encoding="utf-8")
        except Exception:
            pass

    def _read_data(self):
        try:
            if self.db_file.exists():
                content = self.db_file.read_text(encoding="utf-8")
                return json.loads(content) if content.strip() else {}
        except Exception:
            pass
        return {}

    def _write_data(self, data):
        try:
            self.db_file.write_text(json.dumps(data, default=str, indent=2), encoding="utf-8")
        except Exception as e:
            print(f"[LocalDB] Write error: {e}")

    def _load_collection(self, name):
        with self._lock:
            data = self._read_data()
            return data.get(name, [])

    def _save_collection(self, name, docs):
        with self._lock:
            data = self._read_data()
            data[name] = docs
            self._write_data(data)

    def __getitem__(self, item):
        return LocalCollection(item, self)


class LocalClient:
    def __init__(self):
        self.admin = self
        self._local_db = LocalDatabase()

    def command(self, cmd):
        if cmd == "ping":
            return {"ok": 1}
        return {}

    def __getitem__(self, item):
        return self._local_db


_local_client = None


def get_client():
    """
    Returns MongoClient instance or a seamless local storage fallback when MONGO_URI is unset.
    """
    global _client, _local_client
    mongo_uri = os.getenv("MONGO_URI") or getattr(Config, "MONGO_URI", "")
    if mongo_uri:
        if _client is None:
            try:
                _client = MongoClient(
                    mongo_uri,
                    serverSelectionTimeoutMS=4000,
                    connectTimeoutMS=4000,
                    socketTimeoutMS=4000
                )
                _client.admin.command("ping")
                return _client
            except Exception as e:
                print(f"[MongoDB] Remote connection failed: {e}. Falling back to Local Database.")
                _client = None
        else:
            return _client

    if _local_client is None:
        _local_client = LocalClient()
    return _local_client


get_mongo_client = get_client


def get_db():
    """
    Returns the careconnect MongoDB database instance or local fallback database.
    """
    global _db
    client = get_client()
    if isinstance(client, LocalClient):
        return client._local_db
    if client is not None:
        if _db is None:
            db_name = os.getenv("MONGO_DB_NAME") or getattr(Config, "MONGO_DB_NAME", "careconnect")
            _db = client[db_name]
        return _db
    return None


get_mongo_db = get_db


def get_collection(collection_name: str):
    """
    Returns the requested MongoDB / Local collection.
    """
    db = get_db()
    if db is None:
        return None
    if collection_name not in _collections:
        _collections[collection_name] = db[collection_name]
    return _collections[collection_name]


# Collection Accessors
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
    """Ensures essential indexes or local collections are initialized."""
    global _indexes_initialized
    if _indexes_initialized:
        return True
    try:
        db = get_db()
        if db is None:
            return False
        for col_name in ["users", "qr_tokens", "scans", "health_records", "reports", "medical_profiles", "sos_events", "ambulance_requests", "conversations", "conversation_messages"]:
            db[col_name].create_index("id", background=True)
        _indexes_initialized = True
        return True
    except Exception as e:
        print(f"[Database] Index note: {e}")
        return False


def check_db_connection():
    """
    Checks connection status.
    Returns (status: bool, message: str, info: dict)
    """
    client = get_client()
    if isinstance(client, LocalClient):
        users = get_users_collection()
        cnt = users.count_documents({}) if users else 0
        return True, "Local Database Active (Zero-config Ready)", {"users_count": cnt, "engine": "local_storage"}
    
    if client is None:
        return False, "Database not configured", {}
    try:
        client.admin.command("ping")
        db = get_db()
        cnt = db["users"].count_documents({}) if db else 0
        return True, "MongoDB Atlas Connected", {"users_count": cnt, "engine": "mongodb_atlas"}
    except Exception as e:
        return False, f"MongoDB error: {str(e)}", {}


# Legacy compatibility stubs
def query_db(query, args=(), one=False):
    return None if one else []

def execute_db(query, args=()):
    return 0

def get_db_connection():
    return None, "mongodb"
