-- PostgreSQL Setup Script for Django Donation App
-- Run this script as the postgres superuser

-- Create database
CREATE DATABASE donation_db;

-- Create user
CREATE USER donation_user WITH PASSWORD 'your_secure_password_here';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE donation_db TO donation_user;

-- Connect to the donation_db
\c donation_db;

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO donation_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO donation_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO donation_user;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO donation_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO donation_user; 