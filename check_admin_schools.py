#!/usr/bin/env python
"""Check admin accounts and their schools"""

import sqlite3
import os

DATABASE = os.path.join(os.path.dirname(__file__), 'instance', 'vishnorex.db')

try:
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    
    print("=" * 60)
    print("ADMIN ACCOUNTS")
    print("=" * 60)
    cursor.execute('SELECT id, username, school_id FROM admins LIMIT 20')
    rows = cursor.fetchall()
    
    if not rows:
        print("No admins found!")
    else:
        for row in rows:
            print(f"ID: {row[0]}, Username: {row[1]}, School ID: {row[2]}")
    
    print("\n" + "=" * 60)
    print("SCHOOLS")
    print("=" * 60)
    cursor.execute('SELECT id, name FROM schools')
    for row in cursor.fetchall():
        # Count staff for this school
        cursor.execute('SELECT COUNT(*) FROM staff WHERE school_id = ?', (row[0],))
        staff_count = cursor.fetchone()[0]
        # Count periods for this school
        cursor.execute('SELECT COUNT(*) FROM timetable_periods WHERE school_id = ?', (row[0],))
        periods_count = cursor.fetchone()[0]
        print(f"ID: {row[0]}, Name: {row[1]}, Staff: {staff_count}, Periods: {periods_count}")
    
    db.close()
    print("\n✓ Database analysis complete")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
