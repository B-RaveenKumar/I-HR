#!/usr/bin/env python
"""Direct database test without Flask context"""

import sqlite3
import os

DATABASE = os.path.join(os.path.dirname(__file__), 'instance', 'vishnorex.db')

def test_database():
    try:
        # Check if database file exists
        if not os.path.exists(DATABASE):
            print(f"ERROR: Database file not found at {DATABASE}")
            return
        
        # Connect directly without Flask
        db = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
        cursor = db.cursor()
        
        # Check periods
        print("=" * 60)
        print("CHECKING PERIODS TABLE")
        print("=" * 60)
        try:
            cursor.execute('SELECT COUNT(*) as count FROM timetable_periods')
            count = cursor.fetchone()[0]
            print(f"Total periods in database: {count}")
            
            if count > 0:
                cursor.execute('SELECT * FROM timetable_periods LIMIT 5')
                for p in cursor.fetchall():
                    print(f"  Period {p[1]}: {p[2]} ({p[3]} - {p[4]})")
            else:
                print("  No periods found - you need to add periods first!")
        except Exception as e:
            print(f"  Error: {e}")
        
        # Check staff
        print("\n" + "=" * 60)
        print("CHECKING STAFF TABLE")
        print("=" * 60)
        try:
            cursor.execute('SELECT COUNT(*) as count FROM staff WHERE school_id=1')
            count = cursor.fetchone()[0]
            print(f"Total staff for school_id=1: {count}")
            
            if count > 0:
                cursor.execute('SELECT id, staff_id, full_name, department FROM staff WHERE school_id=1 LIMIT 5')
                for s in cursor.fetchall():
                    print(f"  {s[1]}: {s[2]} ({s[3]})")
            else:
                print("  No staff found - you need to add staff first!")
        except Exception as e:
            print(f"  Error: {e}")
        
        # Check schools
        print("\n" + "=" * 60)
        print("CHECKING SCHOOLS")
        print("=" * 60)
        try:
            cursor.execute('SELECT COUNT(*) as count FROM school')
            count = cursor.fetchone()[0]
            print(f"Total schools: {count}")
            
            if count > 0:
                cursor.execute('SELECT id, school_name FROM school LIMIT 3')
                for s in cursor.fetchall():
                    print(f"  School {s[0]}: {s[1]}")
        except Exception as e:
            print(f"  Error: {e}")
        
        db.close()
        print("\n" + "=" * 60)
        print("DATABASE CONNECTION: OK ✓")
        print("=" * 60)
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_database()
