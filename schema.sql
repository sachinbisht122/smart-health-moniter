-- schema.sql

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS health_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    record_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    age INTEGER,
    systolic_bp INTEGER,
    fasting_glucose INTEGER,
    smoking_history TEXT,
    physical_activity TEXT,
    risk_score REAL,
    status TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    record_id INTEGER NOT NULL,
    alert_type TEXT,
    message TEXT,
    severity TEXT, -- 'urgent', 'watch', 'opportunity'
    is_read BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (record_id) REFERENCES health_records(id)
);

CREATE TABLE IF NOT EXISTS care_plan_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    note_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS model_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT,
    accuracy REAL,
    f1_score REAL,
    samples INTEGER,
    last_synced TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial demo user
INSERT OR IGNORE INTO users (id, email, password_hash) VALUES (1, 'demo@vigilia.health', 'dummy_hash');