-- ====================================================================
-- CARECONNECT DATABASE SCHEMA (PostgreSQL)
-- AI-Powered Healthcare Assistance Platform
-- ====================================================================

-- Create Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. USERS TABLE
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

-- 2. SCANS TABLE
CREATE TABLE IF NOT EXISTS scans (
    id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scan_type VARCHAR(50) NOT NULL, -- Chest X-Ray, Skin Lesion, Retinal, General
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

-- 3. REPORTS TABLE
CREATE TABLE IF NOT EXISTS reports (
    id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scan_id VARCHAR(64) REFERENCES scans(id) ON DELETE SET NULL,
    report_type VARCHAR(50) NOT NULL, -- SCAN_REPORT, HEALTH_SUMMARY, LAB_EXPLANATION
    title VARCHAR(255) NOT NULL,
    file_path VARCHAR(500),
    content_json JSONB,
    summary_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at DESC);

-- 4. HEALTH RECORDS TABLE
CREATE TABLE IF NOT EXISTS health_records (
    id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL, -- Allergy, Condition, Medication, History, Note
    title VARCHAR(255) NOT NULL,
    details TEXT,
    severity VARCHAR(30), -- Mild, Moderate, Severe
    start_date VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_health_records_user_id ON health_records(user_id);

-- 5. CONVERSATIONS TABLE (AI Chat)
CREATE TABLE IF NOT EXISTS conversations (
    id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) DEFAULT 'Health Inquiry',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);

-- 6. CONVERSATION MESSAGES TABLE
CREATE TABLE IF NOT EXISTS conversation_messages (
    id VARCHAR(64) PRIMARY KEY,
    conversation_id VARCHAR(64) NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender VARCHAR(20) NOT NULL, -- 'user' or 'assistant'
    message TEXT NOT NULL,
    triage_level VARCHAR(20), -- 'LOW', 'MODERATE', 'URGENT', NULL
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_conv_messages_conv_id ON conversation_messages(conversation_id);
