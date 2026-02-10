#!/usr/bin/env python
"""Diagnostic script to check timetable system state"""

import sqlite3
import os
from pathlib import Path

DATABASE = os.path.join(os.path.dirname(__file__), 'instance', 'vishnorex.db')

def check_database():
    """Check database state"""
    if not os.path.exists(DATABASE):
        print("❌ DATABASE NOT FOUND:", DATABASE)
        return False
    
    print("✅ Database found:", DATABASE)
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    
    print("\n" + "=" * 70)
    print("SCHOOLS & STAFF COUNT")
    print("=" * 70)
    
    cursor.execute('''
        SELECT id, name FROM schools LIMIT 10
    ''')
    
    schools = cursor.fetchall()
    if not schools:
        print("❌ NO SCHOOLS FOUND - Database is empty!")
        return False
    
    for school_id, school_name in schools:
        cursor.execute('SELECT COUNT(*) FROM staff WHERE school_id = ?', (school_id,))
        staff_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM timetable_periods WHERE school_id = ?', (school_id,))
        periods_count = cursor.fetchone()[0]
        
        print(f"✓ School ID {school_id}: '{school_name}'")
        print(f"  - Staff: {staff_count}")
        print(f"  - Periods: {periods_count}")
    
    print("\n" + "=" * 70)
    print("ADMIN ACCOUNTS")
    print("=" * 70)
    
    cursor.execute('SELECT id, username, school_id FROM admins LIMIT 10')
    admins = cursor.fetchall()
    
    if not admins:
        print("❌ NO ADMIN ACCOUNTS FOUND")
    else:
        for admin_id, username, school_id in admins:
            print(f"✓ Admin: {username} (School ID: {school_id})")
    
    db.close()
    return True

if __name__ == '__main__':
    print("\n🔍 TIMETABLE SYSTEM DIAGNOSTIC\n")
    check_database()
    print("\n✓ Diagnostic complete\n")
