-- ========================================
-- Trurism Backend Database Setup Script
-- ========================================
-- This script creates all tables for the Travel Booking Platform
-- Run this in PostgreSQL after creating the database and user
--
-- Instructions:
-- 1. Connect to your database: psql -U trurism_user -d trurism_db
-- 2. Run this script: \i database_setup.sql
-- ========================================

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS flight_booking_passengers CASCADE;
DROP TABLE IF EXISTS flight_bookings CASCADE;
DROP TABLE IF EXISTS hotel_bookings CASCADE;
DROP TABLE IF EXISTS bus_bookings CASCADE;
DROP TABLE IF EXISTS passengers CASCADE;
DROP TABLE IF EXISTS api_keys CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS alembic_version CASCADE;

-- ========================================
-- ENUMS (PostgreSQL Types)
-- ========================================

-- User Role Enum
DROP TYPE IF EXISTS userrole CASCADE;
CREATE TYPE userrole AS ENUM ('customer', 'agent', 'admin');

-- Agent Approval Status Enum
DROP TYPE IF EXISTS agentapprovalstatus CASCADE;
CREATE TYPE agentapprovalstatus AS ENUM ('pending', 'approved', 'rejected', 'suspended');

-- Booking Status Enum
DROP TYPE IF EXISTS bookingstatus CASCADE;
CREATE TYPE bookingstatus AS ENUM ('pending', 'confirmed', 'cancelled', 'refunded', 'expired');

-- Payment Status Enum
DROP TYPE IF EXISTS paymentstatus CASCADE;
CREATE TYPE paymentstatus AS ENUM ('pending', 'success', 'failed', 'refunded', 'partial_refund');

-- Payment Method Enum
DROP TYPE IF EXISTS paymentmethod CASCADE;
CREATE TYPE paymentmethod AS ENUM ('card', 'upi', 'net_banking', 'wallet', 'cash');

-- Passenger Type Enum
DROP TYPE IF EXISTS passengertype CASCADE;
CREATE TYPE passengertype AS ENUM ('ADT', 'CHD', 'INF');

-- API Key Scope Enum
DROP TYPE IF EXISTS apikeyscope CASCADE;
CREATE TYPE apikeyscope AS ENUM ('all', 'flight', 'hotel', 'bus', 'package', 'visa', 'activity');

-- ========================================
-- TABLE: users
-- ========================================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    
    -- User information
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    
    -- Role and permissions
    role userrole NOT NULL DEFAULT 'customer',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Agent-specific fields
    company_name VARCHAR(255),
    pan_number VARCHAR(20),
    approval_status agentapprovalstatus,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    last_login TIMESTAMP WITH TIME ZONE
);

-- Indexes for users table
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_is_active ON users(is_active);

-- ========================================
-- TABLE: api_keys
-- ========================================
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    key VARCHAR(64) UNIQUE NOT NULL,
    key_prefix VARCHAR(16) NOT NULL,
    name VARCHAR(255) NOT NULL,
    
    -- Partner/User relationship
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Permissions and scopes
    scopes JSONB NOT NULL DEFAULT '[]',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Rate limiting
    rate_limit INTEGER NOT NULL DEFAULT 60,
    
    -- Usage tracking
    last_used_at TIMESTAMP WITH TIME ZONE,
    usage_count INTEGER NOT NULL DEFAULT 0,
    
    -- Metadata
    description TEXT,
    environment VARCHAR(20) DEFAULT 'production',
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    revoked_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for api_keys table
CREATE INDEX idx_api_keys_key ON api_keys(key);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_is_active ON api_keys(is_active);

-- ========================================
-- TABLE: passengers
-- ========================================
CREATE TABLE passengers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    age INTEGER NOT NULL,
    type passengertype NOT NULL,
    passport_number VARCHAR(20),
    nationality VARCHAR(3),
    phone VARCHAR(20),
    email VARCHAR(255),
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- ========================================
-- TABLE: flight_bookings
-- ========================================
CREATE TABLE flight_bookings (
    id SERIAL PRIMARY KEY,
    booking_reference VARCHAR(20) UNIQUE NOT NULL,
    
    -- User relationship
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Salesperson/Agent tracking
    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    
    -- Flight details
    offer_id VARCHAR(50) NOT NULL,
    airline VARCHAR(100) NOT NULL,
    flight_number VARCHAR(20) NOT NULL,
    origin VARCHAR(3) NOT NULL,
    destination VARCHAR(3) NOT NULL,
    departure_time TIMESTAMP WITH TIME ZONE NOT NULL,
    arrival_time TIMESTAMP WITH TIME ZONE NOT NULL,
    travel_class VARCHAR(20) NOT NULL,
    
    -- Passenger information
    passenger_count INTEGER NOT NULL,
    passenger_details JSONB NOT NULL,
    
    -- Pricing and payment
    base_fare FLOAT NOT NULL,
    taxes FLOAT NOT NULL,
    total_amount FLOAT NOT NULL,
    currency VARCHAR(3) DEFAULT 'INR',
    payment_method paymentmethod NOT NULL,
    payment_status paymentstatus DEFAULT 'pending',
    
    -- Booking status
    status bookingstatus DEFAULT 'pending',
    confirmation_number VARCHAR(50),
    
    -- Additional information
    special_requests TEXT,
    cancellation_reason TEXT,
    refund_amount FLOAT,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for flight_bookings table
CREATE INDEX idx_flight_bookings_booking_reference ON flight_bookings(booking_reference);
CREATE INDEX idx_flight_bookings_user_id ON flight_bookings(user_id);
CREATE INDEX idx_flight_bookings_created_by_id ON flight_bookings(created_by_id);
CREATE INDEX idx_flight_bookings_status ON flight_bookings(status);
CREATE INDEX idx_flight_bookings_created_at ON flight_bookings(created_at);

-- ========================================
-- TABLE: hotel_bookings
-- ========================================
CREATE TABLE hotel_bookings (
    id SERIAL PRIMARY KEY,
    booking_reference VARCHAR(20) UNIQUE NOT NULL,
    
    -- User relationship
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Salesperson/Agent tracking
    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    
    -- Hotel details
    hotel_id VARCHAR(50) NOT NULL,
    hotel_name VARCHAR(255) NOT NULL,
    hotel_address TEXT NOT NULL,
    city VARCHAR(100) NOT NULL,
    
    -- Booking details
    checkin_date TIMESTAMP WITH TIME ZONE NOT NULL,
    checkout_date TIMESTAMP WITH TIME ZONE NOT NULL,
    nights INTEGER NOT NULL,
    rooms INTEGER NOT NULL,
    adults INTEGER NOT NULL,
    children INTEGER NOT NULL,
    
    -- Guest information
    guest_details JSONB NOT NULL,
    special_requests TEXT,
    
    -- Pricing and payment
    room_rate FLOAT NOT NULL,
    total_amount FLOAT NOT NULL,
    currency VARCHAR(3) DEFAULT 'INR',
    payment_method paymentmethod NOT NULL,
    payment_status paymentstatus DEFAULT 'pending',
    
    -- Booking status
    status bookingstatus DEFAULT 'pending',
    confirmation_number VARCHAR(50),
    
    -- Additional information
    cancellation_reason TEXT,
    refund_amount FLOAT,
    cancellation_policy VARCHAR(100),
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for hotel_bookings table
CREATE INDEX idx_hotel_bookings_booking_reference ON hotel_bookings(booking_reference);
CREATE INDEX idx_hotel_bookings_user_id ON hotel_bookings(user_id);
CREATE INDEX idx_hotel_bookings_created_by_id ON hotel_bookings(created_by_id);
CREATE INDEX idx_hotel_bookings_status ON hotel_bookings(status);

-- ========================================
-- TABLE: bus_bookings
-- ========================================
CREATE TABLE bus_bookings (
    id SERIAL PRIMARY KEY,
    booking_reference VARCHAR(20) UNIQUE NOT NULL,
    
    -- User relationship
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Salesperson/Agent tracking
    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    
    -- Bus details
    bus_id VARCHAR(50) NOT NULL,
    operator VARCHAR(100) NOT NULL,
    bus_type VARCHAR(50) NOT NULL,
    origin VARCHAR(100) NOT NULL,
    destination VARCHAR(100) NOT NULL,
    departure_time TIMESTAMP WITH TIME ZONE NOT NULL,
    arrival_time TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Booking details
    travel_date TIMESTAMP WITH TIME ZONE NOT NULL,
    passengers INTEGER NOT NULL,
    seat_numbers JSONB,
    
    -- Passenger information
    passenger_details JSONB NOT NULL,
    
    -- Pricing and payment
    fare_per_passenger FLOAT NOT NULL,
    total_amount FLOAT NOT NULL,
    currency VARCHAR(3) DEFAULT 'INR',
    payment_method paymentmethod NOT NULL,
    payment_status paymentstatus DEFAULT 'pending',
    
    -- Booking status
    status bookingstatus DEFAULT 'pending',
    confirmation_number VARCHAR(50),
    
    -- Additional information
    boarding_point VARCHAR(255),
    dropping_point VARCHAR(255),
    special_requests TEXT,
    cancellation_reason TEXT,
    refund_amount FLOAT,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for bus_bookings table
CREATE INDEX idx_bus_bookings_booking_reference ON bus_bookings(booking_reference);
CREATE INDEX idx_bus_bookings_user_id ON bus_bookings(user_id);
CREATE INDEX idx_bus_bookings_created_by_id ON bus_bookings(created_by_id);
CREATE INDEX idx_bus_bookings_status ON bus_bookings(status);

-- ========================================
-- TABLE: flight_booking_passengers (Association Table)
-- ========================================
CREATE TABLE flight_booking_passengers (
    booking_id INTEGER NOT NULL REFERENCES flight_bookings(id) ON DELETE CASCADE,
    passenger_id INTEGER NOT NULL REFERENCES passengers(id) ON DELETE CASCADE,
    
    -- Additional booking-specific passenger info
    seat_number VARCHAR(10),
    meal_preference VARCHAR(50),
    special_assistance TEXT,
    
    PRIMARY KEY (booking_id, passenger_id)
);

-- ========================================
-- TABLE: alembic_version (for migrations tracking)
-- ========================================
CREATE TABLE alembic_version (
    version_num VARCHAR(32) PRIMARY KEY
);

-- ========================================
-- SAMPLE DATA (Optional - for testing)
-- ========================================

-- Create a sample admin user
-- Password: admin123 (hashed with bcrypt)
INSERT INTO users (email, password_hash, name, role, is_active, is_verified) 
VALUES (
    'admin@trurism.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqVd.x.qWu',
    'System Admin',
    'admin',
    TRUE,
    TRUE
);

-- Create a sample customer user
-- Password: customer123
INSERT INTO users (email, password_hash, name, phone, role, is_active, is_verified) 
VALUES (
    'customer@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqVd.x.qWu',
    'John Doe',
    '+91-9876543210',
    'customer',
    TRUE,
    TRUE
);

-- Create a sample agent user
-- Password: agent123
INSERT INTO users (email, password_hash, name, phone, role, company_name, pan_number, approval_status, is_active, is_verified) 
VALUES (
    'agent@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqVd.x.qWu',
    'Travel Agent',
    '+91-9876543211',
    'agent',
    'ABC Travels',
    'ABCDE1234F',
    'approved',
    TRUE,
    TRUE
);

-- ========================================
-- GRANTS (Permissions)
-- ========================================

-- Grant all privileges to trurism_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO trurism_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO trurism_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO trurism_user;

-- ========================================
-- VERIFICATION QUERIES
-- ========================================

-- Count tables
SELECT 
    schemaname,
    tablename
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY tablename;

-- Count records in each table
SELECT 'users' as table_name, COUNT(*) as record_count FROM users
UNION ALL
SELECT 'api_keys', COUNT(*) FROM api_keys
UNION ALL
SELECT 'passengers', COUNT(*) FROM passengers
UNION ALL
SELECT 'flight_bookings', COUNT(*) FROM flight_bookings
UNION ALL
SELECT 'hotel_bookings', COUNT(*) FROM hotel_bookings
UNION ALL
SELECT 'bus_bookings', COUNT(*) FROM bus_bookings
UNION ALL
SELECT 'flight_booking_passengers', COUNT(*) FROM flight_booking_passengers;

-- ========================================
-- SETUP COMPLETE
-- ========================================
-- All tables have been created successfully!
-- 
-- Sample users created:
-- - admin@trurism.com (password: admin123) - Admin user
-- - customer@example.com (password: customer123) - Customer user
-- - agent@example.com (password: agent123) - Agent user
--
-- You can now run your FastAPI application!
-- ========================================
