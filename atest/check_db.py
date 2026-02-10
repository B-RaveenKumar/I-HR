#!/usr/bin/env python3
"""
Quick script to check database tables and sync institution timings
"""

import sqlite3
import sys
import os

def main():
    db_path = "vishnorex.db"
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("=== DATABASE TABLES ===")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        for table in tables:
            print(f"  - {table['name']}")
        
        print("\n=== INSTITUTION SETTINGS ===")
        try:
            cursor.execute("SELECT * FROM institution_settings")
            settings = cursor.fetchall()
            for setting in settings:
                print(f"  - {setting['setting_name']}: {setting['setting_value']}")
        except Exception as e:
            print(f"  Error: {e}")
        
        print("\n=== SHIFT DEFINITIONS ===")
        try:
            cursor.execute("SELECT * FROM shift_definitions")
            shifts = cursor.fetchall()
            if shifts:
                for shift in shifts:
                    print(f"  - {shift['shift_type']}: {shift['start_time']} - {shift['end_time']}")
            else:
                print("  No shift definitions found")
        except Exception as e:
            print(f"  Error: {e}")
            
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
