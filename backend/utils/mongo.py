"""
CareConnect MongoDB utilities module.
Re-exports centralized MongoDB database functions from backend.utils.database.
"""
from utils.database import (
    get_client,
    get_mongo_client,
    get_db,
    get_mongo_db,
    get_collection,
    get_users_collection,
    get_medical_profiles_collection,
    get_qr_tokens_collection,
    get_access_logs_collection,
    get_sos_events_collection,
    get_scans_collection,
    get_reports_collection,
    get_health_records_collection,
    get_ambulance_requests_collection,
    get_conversations_collection,
    get_conversation_messages_collection,
    init_db,
    check_db_connection
)

__all__ = [
    "get_client",
    "get_mongo_client",
    "get_db",
    "get_mongo_db",
    "get_collection",
    "get_users_collection",
    "get_medical_profiles_collection",
    "get_qr_tokens_collection",
    "get_access_logs_collection",
    "get_sos_events_collection",
    "get_scans_collection",
    "get_reports_collection",
    "get_health_records_collection",
    "get_ambulance_requests_collection",
    "get_conversations_collection",
    "get_conversation_messages_collection",
    "init_db",
    "check_db_connection"
]
