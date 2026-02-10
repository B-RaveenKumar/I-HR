#!/usr/bin/env python3

from app import app
from database import get_db

def check_database_schema():
    """Check database schema and available data"""
    with app.app_context():
        db = get_db()
        
        print("=== DATABASE SCHEMA ANALYSIS ===")
        print("\n📋 Available Tables:")
        tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        for table in tables:
            print(f"  - {table[0]}")
        
        print("\n📊 Key Tables Analysis:")
        
        # Check attendance table structure
        print("\n🔍 ATTENDANCE Table:")
        try:
            columns = db.execute("PRAGMA table_info(attendance)").fetchall()
            for col in columns:
                print(f"  - {col[1]}: {col[2]}")
        except Exception as e:
            print(f"  Error: {e}")
        
        # Check leave_applications table structure
        print("\n🔍 LEAVE_APPLICATIONS Table:")
        try:
            columns = db.execute("PRAGMA table_info(leave_applications)").fetchall()
            for col in columns:
                print(f"  - {col[1]}: {col[2]}")
        except Exception as e:
            print(f"  Error: {e}")
            
        # Check on_duty_applications table structure
        print("\n🔍 ON_DUTY_APPLICATIONS Table:")
        try:
            columns = db.execute("PRAGMA table_info(on_duty_applications)").fetchall()
            for col in columns:
                print(f"  - {col[1]}: {col[2]}")
        except Exception as e:
            print(f"  Error: {e}")
            
        # Check permission_applications table structure
        print("\n🔍 PERMISSION_APPLICATIONS Table:")
        try:
            columns = db.execute("PRAGMA table_info(permission_applications)").fetchall()
            for col in columns:
                print(f"  - {col[1]}: {col[2]}")
        except Exception as e:
            print(f"  Error: {e}")
            
        # Check staff table structure
        print("\n🔍 STAFF Table:")
        try:
            columns = db.execute("PRAGMA table_info(staff)").fetchall()
            for col in columns:
                print(f"  - {col[1]}: {col[2]}")
        except Exception as e:
            print(f"  Error: {e}")
            
        # Sample data check
        print("\n📈 Sample Data Analysis:")
        
        # Check attendance status values
        print("\nAttendance Status Values:")
        try:
            statuses = db.execute("SELECT DISTINCT status FROM attendance LIMIT 10").fetchall()
            for status in statuses:
                print(f"  - {status[0]}")
        except Exception as e:
            print(f"  Error: {e}")
            
        # Check departments
        print("\nAvailable Departments:")
        try:
            departments = db.execute("SELECT DISTINCT department FROM staff WHERE department IS NOT NULL AND department != '' LIMIT 10").fetchall()
            for dept in departments:
                print(f"  - {dept[0]}")
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == '__main__':
    check_database_schema()