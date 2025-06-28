#!/usr/bin/env python
"""
PostgreSQL Setup Script for Django Donation System
This script helps set up PostgreSQL database for the donation system.
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database():
    """Create PostgreSQL database and user for the donation system."""
    
    # Database configuration
    DB_NAME = os.getenv('DB_NAME', 'donation_db')
    DB_USER = os.getenv('DB_USER', 'donation_user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'donation_password')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    
    # Connect to PostgreSQL server
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user='postgres',  # Default superuser
            password=os.getenv('POSTGRES_PASSWORD', ''),
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print(f"Connected to PostgreSQL server at {DB_HOST}:{DB_PORT}")
        
        # Create user if not exists
        try:
            cursor.execute(f"CREATE USER {DB_USER} WITH PASSWORD '{DB_PASSWORD}';")
            print(f"Created user: {DB_USER}")
        except psycopg2.errors.DuplicateObject:
            print(f"User {DB_USER} already exists")
        
        # Create database if not exists
        try:
            cursor.execute(f"CREATE DATABASE {DB_NAME} OWNER {DB_USER};")
            print(f"Created database: {DB_NAME}")
        except psycopg2.errors.DuplicateDatabase:
            print(f"Database {DB_NAME} already exists")
        
        # Grant privileges
        cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_USER};")
        print(f"Granted privileges to {DB_USER} on {DB_NAME}")
        
        cursor.close()
        conn.close()
        
        print("\n✅ PostgreSQL setup completed successfully!")
        print(f"Database: {DB_NAME}")
        print(f"User: {DB_USER}")
        print(f"Host: {DB_HOST}:{DB_PORT}")
        
    except Exception as e:
        print(f"❌ Error setting up PostgreSQL: {e}")
        sys.exit(1)

def test_connection():
    """Test the database connection."""
    
    DB_NAME = os.getenv('DB_NAME', 'donation_db')
    DB_USER = os.getenv('DB_USER', 'donation_user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'donation_password')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Database connection successful!")
        print(f"PostgreSQL version: {version[0]}")
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

if __name__ == "__main__":
    print("🐘 PostgreSQL Setup for Django Donation System")
    print("=" * 50)
    
    action = input("Choose action:\n1. Create database and user\n2. Test connection\n3. Both\nEnter choice (1-3): ")
    
    if action in ['1', '3']:
        create_database()
    
    if action in ['2', '3']:
        print("\n" + "=" * 50)
        test_connection() 