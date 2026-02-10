#!/usr/bin/env python3
"""
Test script for Department Shifts functionality
"""
import sqlite3
import requests
import json

def check_database_table():
    """Check if department_shift_mappings table exists and its structure"""
    try:
        conn = sqlite3.connect('vishnorex.db')
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='department_shift_mappings'
        """)
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("✓ department_shift_mappings table exists")
            
            # Check table structure
            cursor.execute("PRAGMA table_info(department_shift_mappings)")
            columns = cursor.fetchall()
            print("Table structure:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            
            # Check existing data
            cursor.execute("SELECT COUNT(*) FROM department_shift_mappings")
            count = cursor.fetchone()[0]
            print(f"Existing records: {count}")
            
        else:
            print("✗ department_shift_mappings table does NOT exist")
            
            # Check what tables do exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print("Available tables:")
            for table in tables:
                print(f"  - {table[0]}")
        
        conn.close()
        return table_exists is not None
        
    except Exception as e:
        print(f"Error checking database: {e}")
        return False

def test_api_endpoint():
    """Test the API endpoint for department shifts"""
    try:
        # Test GET request
        response = requests.get('http://127.0.0.1:5000/api/department_shifts')
        print(f"API GET status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"API response: {data}")
        else:
            print(f"API error: {response.text}")
            
    except Exception as e:
        print(f"Error testing API: {e}")

def create_test_mapping():
    """Create a test department mapping"""
    try:
        conn = sqlite3.connect('vishnorex.db')
        cursor = conn.cursor()
        
        # Insert test data
        cursor.execute("""
            INSERT OR REPLACE INTO department_shift_mappings 
            (school_id, department, default_shift_type, created_at, updated_at)
            VALUES (1, 'IT', 'general', datetime('now'), datetime('now'))
        """)
        
        cursor.execute("""
            INSERT OR REPLACE INTO department_shift_mappings 
            (school_id, department, default_shift_type, created_at, updated_at)
            VALUES (1, 'Teaching', 'morning', datetime('now'), datetime('now'))
        """)
        
        conn.commit()
        conn.close()
        print("✓ Test mappings created successfully")
        
    except Exception as e:
        print(f"Error creating test mappings: {e}")

if __name__ == "__main__":
    print("=== Department Shifts Test ===")
    print()
    
    print("1. Checking database table...")
    table_exists = check_database_table()
    print()
    
    if table_exists:
        print("2. Creating test mappings...")
        create_test_mapping()
        print()
        
        print("3. Testing API endpoint...")
        test_api_endpoint()
    else:
        print("❌ Cannot proceed - database table missing")
    
    print("\n=== Test Complete ===")
