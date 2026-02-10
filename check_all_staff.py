#!/usr/bin/env python
"""Check all schools and their staff"""

import sqlite3
import os

DATABASE = os.path.join(os.path.dirname(__file__), 'instance', 'vishnorex.db')

def test_database():
    try:
        db = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
        cursor = db.cursor()
        
        # Check which table has school info
        print("Checking database schema...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%school%'")
        school_tables = cursor.fetchall()
        print(f"School-related tables: {[t[0] for t in school_tables]}")
        
        # Get all staff by school
        print("\n" + "=" * 60)
        print("ALL STAFF BY SCHOOL")
        print("=" * 60)
        cursor.execute('''
            SELECT DISTINCT school_id, COUNT(*) as count 
            FROM staff 
            GROUP BY school_id
        ''')
        for row in cursor.fetchall():
            print(f"School {row[0]}: {row[1]} staff members")
            
            # Get first 5 staff
            cursor.execute('''
                SELECT id, staff_id, full_name, department 
                FROM staff 
                WHERE school_id = ? 
                LIMIT 5
            ''', (row[0],))
            for s in cursor.fetchall():
                print(f"  - {s[1]}: {s[2]} ({s[3]})")
        
        # Check periods
        print("\n" + "=" * 60)
        print("PERIODS IN DATABASE")
        print("=" * 60)
        cursor.execute('SELECT COUNT(*) as count FROM timetable_periods')
        count = cursor.fetchone()[0]
        print(f"Total periods: {count}")
        
        cursor.execute('SELECT * FROM timetable_periods')
        for p in cursor.fetchall():
            print(f"  Period {p[1]}: {p[2]} ({p[3]} - {p[4]})")
        
        db.close()
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_database()
