-- Gujarat Police Citizen Feedback System
-- Database Schema

CREATE DATABASE IF NOT EXISTS gujarat_police_feedback CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE gujarat_police_feedback;

-- Police Stations Table
CREATE TABLE IF NOT EXISTS police_stations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    station_name VARCHAR(200) NOT NULL,
    district VARCHAR(100) NOT NULL,
    address TEXT,
    contact_number VARCHAR(15),
    station_code VARCHAR(20) UNIQUE NOT NULL,
    qr_code_path VARCHAR(500),
    qr_code_url VARCHAR(500),
    is_active TINYINT(1) DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Officers Table
CREATE TABLE IF NOT EXISTS officers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    badge_number VARCHAR(50) UNIQUE,
    email VARCHAR(200) UNIQUE NOT NULL,
    password_hash VARCHAR(500) NOT NULL,
    role ENUM('admin', 'officer') DEFAULT 'officer',
    station_id INT,
    phone VARCHAR(15),
    rank VARCHAR(100),
    is_active TINYINT(1) DEFAULT 1,
    last_login DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (station_id) REFERENCES police_stations(id) ON DELETE SET NULL
);

-- Feedback Table
CREATE TABLE IF NOT EXISTS feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    station_id INT NOT NULL,
    acknowledgment_id VARCHAR(50) UNIQUE NOT NULL,
    citizen_name VARCHAR(200),
    mobile VARCHAR(15),
    gender ENUM('male', 'female', 'other', 'prefer_not_to_say'),
    age_group ENUM('under_18', '18_25', '26_35', '36_45', '46_60', 'above_60'),
    behavior_rating TINYINT CHECK (behavior_rating BETWEEN 1 AND 5),
    response_rating TINYINT CHECK (response_rating BETWEEN 1 AND 5),
    cleanliness_rating TINYINT CHECK (cleanliness_rating BETWEEN 1 AND 5),
    helpfulness_rating TINYINT CHECK (helpfulness_rating BETWEEN 1 AND 5),
    transparency_rating TINYINT CHECK (transparency_rating BETWEEN 1 AND 5),
    overall_rating TINYINT CHECK (overall_rating BETWEEN 1 AND 5),
    feedback_text TEXT,
    complaint TEXT,
    complaint_category ENUM('corruption', 'misconduct', 'delay', 'rude_behavior', 'other'),
    sentiment ENUM('positive', 'neutral', 'negative'),
    sentiment_score FLOAT,
    image_path VARCHAR(500),
    ip_address VARCHAR(50),
    is_resolved TINYINT(1) DEFAULT 0,
    resolved_by INT,
    resolved_at DATETIME,
    resolution_note TEXT,
    is_flagged TINYINT(1) DEFAULT 0,
    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (station_id) REFERENCES police_stations(id),
    FOREIGN KEY (resolved_by) REFERENCES officers(id) ON DELETE SET NULL
);

-- Notifications Table
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    officer_id INT,
    message TEXT NOT NULL,
    type ENUM('feedback', 'complaint', 'system') DEFAULT 'feedback',
    is_read TINYINT(1) DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (officer_id) REFERENCES officers(id) ON DELETE CASCADE
);

-- Audit Logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    officer_id INT,
    action VARCHAR(200),
    details TEXT,
    ip_address VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (officer_id) REFERENCES officers(id) ON DELETE SET NULL
);

-- Insert sample police stations
INSERT INTO police_stations (station_name, district, address, contact_number, station_code) VALUES
('Ahmedabad City Police Station', 'Ahmedabad', 'Shahibaug, Ahmedabad - 380004', '079-25621234', 'AMD001'),
('Surat Central Police Station', 'Surat', 'Ring Road, Surat - 395002', '0261-2422234', 'SRT001'),
('Vadodara Sayajigunj Police Station', 'Vadodara', 'Sayajigunj, Vadodara - 390005', '0265-2363234', 'VDR001'),
('Rajkot Police Station', 'Rajkot', 'Dr. Yagnik Road, Rajkot - 360001', '0281-2236234', 'RJT001'),
('Gandhinagar Sector-7 Police Station', 'Gandhinagar', 'Sector-7, Gandhinagar - 382007', '079-23222234', 'GDN001');

-- Insert default admin
INSERT INTO officers (name, badge_number, email, password_hash, role, rank) VALUES
('System Administrator', 'ADMIN001', 'admin@gujaratpolice.gov.in', 
 'scrypt:32768:8:1$salt$hash_placeholder', 'admin', 'Inspector General');

-- Create indexes for performance
CREATE INDEX idx_feedback_station ON feedback(station_id);
CREATE INDEX idx_feedback_submitted ON feedback(submitted_at);
CREATE INDEX idx_feedback_overall ON feedback(overall_rating);
CREATE INDEX idx_officers_email ON officers(email);
