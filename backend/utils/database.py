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
    """Initializes the database schema if tables do not exist."""
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
        """)
        conn.commit()
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
        """)
        conn.commit()

    conn.close()
    print(f"[Database] Initialized tables successfully ({db_type}).")

def query_db(query, args=(), one=False):
    """Convenience helper to query database and return dictionary objects."""
    conn, db_type = get_db_connection()
    # Normalize parameter placeholders if necessary (? for sqlite, %s for postgres)
    if db_type == "postgresql":
        query = query.replace("?", "%s")
    
    cursor = conn.cursor()
    cursor.execute(query, args)
    if query.strip().upper().startswith(("SELECT", "WITH")):
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
