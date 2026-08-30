import os
import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
from config import Config

# Check if PostgreSQL connection is requested and available
USE_POSTGRES = bool(Config.DATABASE_URL and Config.DATABASE_URL.startswith("postgresql"))

if USE_POSTGRES:
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
    except ImportError:
        USE_POSTGRES = False

def get_db_connection():
    """Returns a database connection (PostgreSQL or SQLite)"""
    if USE_POSTGRES:
        try:
            conn = psycopg2.connect(Config.DATABASE_URL, cursor_factory=RealDictCursor)
            return conn, "postgresql"
        except Exception as e:
            print(f"[Database] PostgreSQL connection failed, falling back to SQLite: {e}")
    
    # SQLite local connection
    conn = sqlite3.connect(Config.SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn, "sqlite"

def init_db():
    """Initializes the database schema if tables do not exist and applies migrations."""
    conn, db_type = get_db_connection()
    cursor = conn.cursor()

    if db_type == "postgresql":
        # Create Postgres tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(64) PRIMARY KEY,
                name VARCHAR(120) NOT NULL,
                email VARCHAR(180) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                phone VARCHAR(30),
                blood_group VARCHAR(10),
                emergency_contact VARCHAR(120),
                emergency_phone VARCHAR(30),
                allergies TEXT,
                medications TEXT,
                conditions TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

            CREATE TABLE IF NOT EXISTS scans (
                id VARCHAR(64) PRIMARY KEY,
                user_id VARCHAR(64) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                scan_type VARCHAR(50) NOT NULL,
                image_path VARCHAR(500) NOT NULL,
                image_url VARCHAR(500),
                result VARCHAR(255) NOT NULL,
                confidence FLOAT NOT NULL,
                explanation TEXT NOT NULL,
                possible_meaning TEXT,
                recommendation TEXT NOT NULL,
                warning_signs TEXT,
                disclaimer TEXT NOT NULL,
                status VARCHAR(30) DEFAULT 'COMPLETED',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_scans_user_id ON scans(user_id);
            CREATE INDEX IF NOT EXISTS idx_scans_created_at ON scans(created_at DESC);

            CREATE TABLE IF NOT EXISTS reports (
                id VARCHAR(64) PRIMARY KEY,
                user_id VARCHAR(64) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                scan_id VARCHAR(64) REFERENCES scans(id) ON DELETE SET NULL,
                report_type VARCHAR(50) NOT NULL,
                title VARCHAR(255) NOT NULL,
                file_path VARCHAR(500),
                content_json JSONB,
                summary_text TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id);

            CREATE TABLE IF NOT EXISTS health_records (
                id VARCHAR(64) PRIMARY KEY,
                user_id VARCHAR(64) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                category VARCHAR(50) NOT NULL,
                title VARCHAR(255) NOT NULL,
                details TEXT,
                severity VARCHAR(30),
                start_date VARCHAR(50),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_health_records_user_id ON health_records(user_id);

            CREATE TABLE IF NOT EXISTS conversations (
                id VARCHAR(64) PRIMARY KEY,
                user_id VARCHAR(64) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title VARCHAR(255) DEFAULT 'Health Inquiry',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);

            CREATE TABLE IF NOT EXISTS conversation_messages (
                id VARCHAR(64) PRIMARY KEY,
                conversation_id VARCHAR(64) NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                sender VARCHAR(20) NOT NULL,
                message TEXT NOT NULL,
                triage_level VARCHAR(20),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_conv_messages_conv_id ON conversation_messages(conversation_id);

            CREATE TABLE IF NOT EXISTS medical_profiles (
                id VARCHAR(64) PRIMARY KEY,
                user_id VARCHAR(64) NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                blood_group VARCHAR(10) NOT NULL,
                phone VARCHAR(30) NOT NULL,
                allergies TEXT,
                medications TEXT,
                conditions TEXT,
                emergency_contact VARCHAR(120) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS qr_tokens (
                id VARCHAR(64) PRIMARY KEY,
                token VARCHAR(64) UNIQUE NOT NULL,
                user_id VARCHAR(64) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_qr_tokens_token ON qr_tokens(token);

            CREATE TABLE IF NOT EXISTS sos_events (
                id VARCHAR(64) PRIMARY KEY,
                user_id VARCHAR(64) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                latitude FLOAT,
                longitude FLOAT,
                message TEXT NOT NULL,
                status VARCHAR(30) DEFAULT 'ACTIVE',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_sos_events_user ON sos_events(user_id);

            CREATE TABLE IF NOT EXISTS ambulance_requests (
                id VARCHAR(64) PRIMARY KEY,
                user_id VARCHAR(64) REFERENCES users(id) ON DELETE SET NULL,
                patient_name VARCHAR(120) NOT NULL,
                contact_number VARCHAR(30) NOT NULL,
                emergency_type VARCHAR(50) NOT NULL,
                current_location TEXT NOT NULL,
                additional_details TEXT,
                status VARCHAR(30) DEFAULT 'REQUESTED',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_ambulance_user ON ambulance_requests(user_id);

            CREATE TABLE IF NOT EXISTS access_logs (
                id VARCHAR(64) PRIMARY KEY,
                user_id VARCHAR(64) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                access_type VARCHAR(50) NOT NULL,
                accessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()

        # Check PostgreSQL migrations
        for col, col_type in [("allergies", "TEXT"), ("medications", "TEXT"), ("conditions", "TEXT")]:
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col} {col_type};")
                conn.commit()
            except Exception:
                conn.rollback()

    else:
        # Create SQLite tables
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                phone TEXT,
                blood_group TEXT,
                emergency_contact TEXT,
                emergency_phone TEXT,
                allergies TEXT,
                medications TEXT,
                conditions TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

            CREATE TABLE IF NOT EXISTS scans (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                scan_type TEXT NOT NULL,
                image_path TEXT NOT NULL,
                image_url TEXT,
                result TEXT NOT NULL,
                confidence REAL NOT NULL,
                explanation TEXT NOT NULL,
                possible_meaning TEXT,
                recommendation TEXT NOT NULL,
                warning_signs TEXT,
                disclaimer TEXT NOT NULL,
                status TEXT DEFAULT 'COMPLETED',
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_scans_user_id ON scans(user_id);
            CREATE INDEX IF NOT EXISTS idx_scans_created_at ON scans(created_at DESC);

            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                scan_id TEXT REFERENCES scans(id) ON DELETE SET NULL,
                report_type TEXT NOT NULL,
                title TEXT NOT NULL,
                file_path TEXT,
                content_json TEXT,
                summary_text TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id);

            CREATE TABLE IF NOT EXISTS health_records (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                details TEXT,
                severity TEXT,
                start_date TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_health_records_user_id ON health_records(user_id);

            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title TEXT DEFAULT 'Health Inquiry',
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);

            CREATE TABLE IF NOT EXISTS conversation_messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                sender TEXT NOT NULL,
                message TEXT NOT NULL,
                triage_level TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_conv_messages_conv_id ON conversation_messages(conversation_id);

            CREATE TABLE IF NOT EXISTS medical_profiles (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                blood_group TEXT NOT NULL,
                phone TEXT NOT NULL,
                allergies TEXT,
                medications TEXT,
                conditions TEXT,
                emergency_contact TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS qr_tokens (
                id TEXT PRIMARY KEY,
                token TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_qr_tokens_token ON qr_tokens(token);

            CREATE TABLE IF NOT EXISTS sos_events (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                latitude REAL,
                longitude REAL,
                message TEXT NOT NULL,
                status TEXT DEFAULT 'ACTIVE',
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_sos_events_user ON sos_events(user_id);

            CREATE TABLE IF NOT EXISTS ambulance_requests (
                id TEXT PRIMARY KEY,
                user_id TEXT REFERENCES users(id) ON DELETE SET NULL,
                patient_name TEXT NOT NULL,
                contact_number TEXT NOT NULL,
                emergency_type TEXT NOT NULL,
                current_location TEXT NOT NULL,
                additional_details TEXT,
                status TEXT DEFAULT 'REQUESTED',
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_ambulance_user ON ambulance_requests(user_id);

            CREATE TABLE IF NOT EXISTS access_logs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                access_type TEXT NOT NULL,
                accessed_at TEXT DEFAULT (datetime('now'))
            );
        """)
        conn.commit()

        # Check SQLite migrations for existing users table
        cursor.execute("PRAGMA table_info(users);")
        existing_cols = {row["name"] for row in cursor.fetchall()}
        for col, col_type in [("allergies", "TEXT"), ("medications", "TEXT"), ("conditions", "TEXT"), ("emergency_phone", "TEXT"), ("emergency_contact", "TEXT"), ("blood_group", "TEXT"), ("phone", "TEXT")]:
            if col not in existing_cols:
                try:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type};")
                    conn.commit()
                except Exception as ex:
                    print(f"[Migration] Note: {ex}")

    conn.close()
    print(f"[Database] Initialized tables successfully ({db_type}).")

def query_db(query, args=(), one=False):
    """Convenience helper to query database and return dictionary objects."""
    conn, db_type = get_db_connection()
    if db_type == "postgresql":
        query = query.replace("?", "%s")
    
    cursor = conn.cursor()
    cursor.execute(query, args)
    if query.strip().upper().startswith(("SELECT", "WITH", "PRAGMA")):
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        if db_type == "sqlite":
            result = [dict(row) for row in rows]
        else:
            result = [dict(r) for r in rows]
        return (result[0] if result else None) if one else result
    else:
        conn.commit()
        last_id = getattr(cursor, "lastrowid", None)
        cursor.close()
        conn.close()
        return last_id

def execute_db(query, args=()):
    """Convenience helper to execute insert/update/delete."""
    conn, db_type = get_db_connection()
    if db_type == "postgresql":
        query = query.replace("?", "%s")
    cursor = conn.cursor()
    cursor.execute(query, args)
    conn.commit()
    rowcount = cursor.rowcount
    cursor.close()
    conn.close()
    return rowcount
