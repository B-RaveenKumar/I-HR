#!/usr/bin/env python
"""
Complete Timetable System Diagnostic
Checks database, admins, staff, periods, and API endpoints
"""

import sqlite3
import os
from pathlib import Path

DATABASE = os.path.join(os.path.dirname(__file__), 'instance', 'vishnorex.db')

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def check_database_exists():
    """Check if database file exists"""
    if os.path.exists(DATABASE):
        print(f"✅ Database file exists: {DATABASE}")
        return True
    else:
        print(f"❌ Database file NOT found: {DATABASE}")
        return False

def check_tables(cursor):
    """Check if required tables exist"""
    tables = [
        'schools',
        'admins',
        'staff',
        'timetable_periods',
        'timetable_assignments',
        'timetable_department_permissions'
    ]
    
    print_section("DATABASE TABLES")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = {row[0] for row in cursor.fetchall()}
    
    for table in tables:
        if table in existing_tables:
            print(f"✅ {table}")
        else:
            print(f"❌ {table} (MISSING)")
    
    return len([t for t in tables if t in existing_tables]) == len(tables)

def check_schools_and_data(cursor):
    """Check schools and their associated data"""
    print_section("SCHOOLS & DATA DISTRIBUTION")
    
    cursor.execute('SELECT id, name FROM schools LIMIT 10')
    schools = cursor.fetchall()
    
    if not schools:
        print("❌ NO SCHOOLS FOUND - Database appears empty!")
        return False
    
    total_staff = 0
    total_periods = 0
    
    for school_id, school_name in schools:
        cursor.execute('SELECT COUNT(*) FROM staff WHERE school_id = ?', (school_id,))
        staff_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM timetable_periods WHERE school_id = ?', (school_id,))
        periods_count = cursor.fetchone()[0]
        
        total_staff += staff_count
        total_periods += periods_count
        
        status = "✅" if staff_count > 0 and periods_count > 0 else "⚠️"
        print(f"{status} School {school_id}: '{school_name}'")
        print(f"   └─ Staff: {staff_count}, Periods: {periods_count}")
    
    print(f"\n📊 Total: {total_staff} staff across all schools")
    print(f"📊 Total: {total_periods} periods across all schools")
    
    return total_staff > 0 and total_periods > 0

def check_admins(cursor):
    """Check admin accounts"""
    print_section("ADMIN ACCOUNTS")
    
    cursor.execute('SELECT id, username, school_id FROM admins ORDER BY school_id')
    admins = cursor.fetchall()
    
    if not admins:
        print("❌ NO ADMIN ACCOUNTS - Cannot login!")
        return False
    
    for admin_id, username, school_id in admins:
        print(f"✅ {username:15} → School ID {school_id}")
    
    return len(admins) > 0

def check_staff_by_school(cursor):
    """Check staff distribution by school"""
    print_section("STAFF DISTRIBUTION BY SCHOOL")
    
    cursor.execute('''
        SELECT school_id, COUNT(*) as count
        FROM staff
        GROUP BY school_id
        ORDER BY school_id
    ''')
    
    results = cursor.fetchall()
    
    if not results:
        print("❌ NO STAFF DATA - Database might not be populated!")
        return False
    
    for school_id, count in results:
        status = "✅" if count > 0 else "⚠️"
        print(f"{status} School {school_id}: {count} staff members")
    
    return all(count > 0 for _, count in results)

def check_periods_by_school(cursor):
    """Check periods distribution by school"""
    print_section("PERIODS DISTRIBUTION BY SCHOOL")
    
    cursor.execute('''
        SELECT school_id, COUNT(*) as count
        FROM timetable_periods
        GROUP BY school_id
        ORDER BY school_id
    ''')
    
    results = cursor.fetchall()
    
    if not results:
        print("❌ NO PERIODS - Database might not be populated!")
        return False
    
    for school_id, count in results:
        status = "✅" if count >= 8 else "⚠️"
        print(f"{status} School {school_id}: {count} periods")
    
    return all(count > 0 for _, count in results)

def check_school_id_1_data(cursor):
    """Specifically check school_id=1 data (for common testing)"""
    print_section("SCHOOL ID 1 DETAILED CHECK")
    
    cursor.execute('SELECT name FROM schools WHERE id = 1')
    school = cursor.fetchone()
    
    if not school:
        print("⚠️  School ID 1 does not exist")
        return False
    
    school_name = school[0]
    print(f"✅ School: {school_name}")
    
    cursor.execute('SELECT COUNT(*) FROM admins WHERE school_id = 1')
    admin_count = cursor.fetchone()[0]
    print(f"{'✅' if admin_count > 0 else '⚠️'} Admins: {admin_count}")
    
    cursor.execute('SELECT COUNT(*) FROM staff WHERE school_id = 1')
    staff_count = cursor.fetchone()[0]
    print(f"{'✅' if staff_count > 0 else '❌'} Staff: {staff_count}")
    
    cursor.execute('SELECT COUNT(*) FROM timetable_periods WHERE school_id = 1')
    periods_count = cursor.fetchone()[0]
    print(f"{'✅' if periods_count > 0 else '❌'} Periods: {periods_count}")
    
    cursor.execute('''
        SELECT COUNT(*) FROM timetable_department_permissions 
        WHERE school_id = 1
    ''')
    dept_perms_count = cursor.fetchone()[0]
    print(f"{'✅' if dept_perms_count > 0 else '⚠️'} Department Permissions: {dept_perms_count}")
    
    return staff_count > 0 and periods_count > 0

def main():
    """Run all diagnostics"""
    print("\n" + "🔍 " * 15)
    print("TIMETABLE MANAGEMENT SYSTEM DIAGNOSTIC")
    print("🔍 " * 15)
    
    # Check database existence
    if not check_database_exists():
        print("\n❌ Cannot proceed - database file not found!")
        print("   Run: python populate_db.py")
        return
    
    try:
        db = sqlite3.connect(DATABASE)
        cursor = db.cursor()
        
        # Run all checks
        checks = [
            ("Tables", check_tables(cursor)),
            ("Schools & Data", check_schools_and_data(cursor)),
            ("Admins", check_admins(cursor)),
            ("Staff Distribution", check_staff_by_school(cursor)),
            ("Periods Distribution", check_periods_by_school(cursor)),
            ("School 1 Data", check_school_id_1_data(cursor))
        ]
        
        db.close()
        
        # Summary
        print_section("DIAGNOSTIC SUMMARY")
        
        all_passed = True
        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"{status} {check_name}")
            if not passed:
                all_passed = False
        
        print("\n" + "=" * 70)
        if all_passed:
            print("✅ SYSTEM READY - All checks passed!")
            print("   You can now test the timetable management.")
        else:
            print("⚠️  SYSTEM NEEDS SETUP - Some checks failed!")
            print("   Run: python populate_db.py")
        
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("   Make sure database is not locked by another process.")

if __name__ == '__main__':
    main()
