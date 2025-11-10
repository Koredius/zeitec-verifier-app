-- Zeitec Verifier System Database Schema
-- PostgreSQL 14+

-- ============================================
-- PHASE 1: REGISTRANT MANAGEMENT
-- ============================================

-- Admin users table
CREATE TABLE admins (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Registrant applications table
CREATE TABLE registrants (
    id SERIAL PRIMARY KEY,
    organization_name VARCHAR(200) NOT NULL,
    contact_person VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    country VARCHAR(50) NOT NULL CHECK (country IN ('Nigeria', 'Benin', 'Ghana', 'Kenya', 'South Africa')),
    num_facilities INTEGER,
    total_capacity_kw DECIMAL(10, 2),
    description TEXT,
    business_doc_url VARCHAR(500),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    reviewed_by INTEGER REFERENCES admins(id),
    reviewer_notes TEXT,
    guardian_did VARCHAR(255),  -- DID after approval in Guardian
    CONSTRAINT unique_org_email UNIQUE (organization_name, email)
);

-- ============================================
-- PHASE 2: DEVICE REGISTRATION
-- ============================================

-- Device registry table
CREATE TABLE devices (
    id SERIAL PRIMARY KEY,
    registrant_id INTEGER NOT NULL REFERENCES registrants(id) ON DELETE CASCADE,
    device_id VARCHAR(100) NOT NULL,
    facility_id VARCHAR(100) NOT NULL,
    serial_number VARCHAR(100),
    manufacturer VARCHAR(100),
    model VARCHAR(100),
    capacity_kw DECIMAL(10, 2) NOT NULL CHECK (capacity_kw <= 250),  -- ≤250 kW requirement
    technology VARCHAR(50),
    country VARCHAR(50) NOT NULL,
    grid_connection_point VARCHAR(100),
    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),
    commissioning_date DATE,
    device_hash VARCHAR(64),  -- SHA256 hash of device record
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    reviewed_by INTEGER REFERENCES admins(id),
    reviewer_notes TEXT,
    CONSTRAINT unique_device_facility UNIQUE (device_id, facility_id)
);

-- Supporting documents table
CREATE TABLE device_documents (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    document_type VARCHAR(50) NOT NULL CHECK (document_type IN (
        'owner_declaration', 
        'single_line_diagram', 
        'ppa', 
        'site_photo', 
        'other'
    )),
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_hash VARCHAR(64),  -- SHA256 hash for integrity
    file_size INTEGER,
    mime_type VARCHAR(100),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- PHASE 3: ISSUANCE & VERIFICATION
-- ============================================

-- Issuance submissions table
CREATE TABLE issuance_submissions (
    id SERIAL PRIMARY KEY,
    registrant_id INTEGER NOT NULL REFERENCES registrants(id) ON DELETE CASCADE,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    issuance_period_start TIMESTAMP NOT NULL,
    issuance_period_end TIMESTAMP NOT NULL,
    total_kwh DECIMAL(12, 3),
    num_readings INTEGER,
    csv_file_path VARCHAR(500),
    csv_hash VARCHAR(64),  -- SHA256 of entire CSV file
    registrant_declaration_path VARCHAR(500),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN (
        'pending', 
        'under_review', 
        'approved', 
        'rejected', 
        'duplicate_detected'
    )),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    submitted_by VARCHAR(100),
    deduplication_result JSONB,  -- Store duplicate check results
    verifier_review_id INTEGER,
    CONSTRAINT valid_period CHECK (issuance_period_end > issuance_period_start)
);

-- Deduplication log (stores all auditTrailIds)
CREATE TABLE deduplication_log (
    id SERIAL PRIMARY KEY,
    audit_trail_id VARCHAR(64) NOT NULL UNIQUE,  -- SHA256(deviceId + timestamp + kWh)
    device_id VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    kwh DECIMAL(10, 3) NOT NULL,
    issuance_submission_id INTEGER REFERENCES issuance_submissions(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_device_timestamp UNIQUE (device_id, timestamp)
);

-- Verifier reviews table
CREATE TABLE verifier_reviews (
    id SERIAL PRIMARY KEY,
    issuance_submission_id INTEGER NOT NULL REFERENCES issuance_submissions(id) ON DELETE CASCADE,
    verifier_id INTEGER NOT NULL REFERENCES admins(id),
    decision VARCHAR(20) NOT NULL CHECK (decision IN ('approved', 'rejected')),
    review_notes TEXT,
    checklist JSONB,  -- Store verifier checklist results
    verifier_vc_issued BOOLEAN DEFAULT FALSE,
    verifier_vc_data JSONB,  -- Verifiable Credential data
    reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    measurement_tier VARCHAR(10) DEFAULT '2.3',
    device_scope_confirmed BOOLEAN DEFAULT FALSE,
    grouping_keys_consistent BOOLEAN DEFAULT FALSE,
    no_dedupe_collisions BOOLEAN DEFAULT FALSE
);

-- ============================================
-- AUDIT & ANALYTICS
-- ============================================

-- Audit trail for all system actions
CREATE TABLE audit_trail (
    id SERIAL PRIMARY KEY,
    action_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER,
    performed_by INTEGER REFERENCES admins(id),
    action_details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System analytics
CREATE TABLE analytics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15, 3),
    metric_data JSONB,
    period_start TIMESTAMP,
    period_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

-- Registrants indexes
CREATE INDEX idx_registrants_status ON registrants(status);
CREATE INDEX idx_registrants_country ON registrants(country);
CREATE INDEX idx_registrants_email ON registrants(email);

-- Devices indexes
CREATE INDEX idx_devices_registrant ON devices(registrant_id);
CREATE INDEX idx_devices_status ON devices(status);
CREATE INDEX idx_devices_device_id ON devices(device_id);
CREATE INDEX idx_devices_facility_id ON devices(facility_id);

-- Device documents indexes
CREATE INDEX idx_device_docs_device ON device_documents(device_id);
CREATE INDEX idx_device_docs_type ON device_documents(document_type);

-- Issuance submissions indexes
CREATE INDEX idx_issuance_registrant ON issuance_submissions(registrant_id);
CREATE INDEX idx_issuance_device ON issuance_submissions(device_id);
CREATE INDEX idx_issuance_status ON issuance_submissions(status);
CREATE INDEX idx_issuance_period ON issuance_submissions(issuance_period_start, issuance_period_end);

-- Deduplication log indexes
CREATE INDEX idx_dedupe_audit_trail_id ON deduplication_log(audit_trail_id);
CREATE INDEX idx_dedupe_device_timestamp ON deduplication_log(device_id, timestamp);

-- Verifier reviews indexes
CREATE INDEX idx_reviews_submission ON verifier_reviews(issuance_submission_id);
CREATE INDEX idx_reviews_verifier ON verifier_reviews(verifier_id);

-- Audit trail indexes
CREATE INDEX idx_audit_entity ON audit_trail(entity_type, entity_id);
CREATE INDEX idx_audit_performed_by ON audit_trail(performed_by);
CREATE INDEX idx_audit_created_at ON audit_trail(created_at);

-- ============================================
-- INITIAL DATA
-- ============================================

-- Create default admin account (password: admin123 - CHANGE IN PRODUCTION!)
-- Password hash generated using bcrypt
INSERT INTO admins (username, email, full_name, password_hash) 
VALUES (
    'admin',
    'admin@zeitec.io',
    'System Administrator',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5ztP6kBvZH8Iu'  -- 'admin123'
);
