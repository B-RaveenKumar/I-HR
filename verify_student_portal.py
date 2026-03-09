#!/usr/bin/env python3
"""
Verify Student Portal Installation
This script checks if all components are properly installed
"""

import os
import sqlite3

def check_templates():
    """Check if all template files exist"""
    print("📁 Checking Template Files...")
    
    required_templates = [
        'templates/student/student_login.html',
        'templates/student/student_dashboard.html',
        'templates/student/student_attendance_history.html',
        'templates/student/student_profile.html',
        'templates/student/mark_student_attendance.html'
    ]
    
    all_exist = True
    for template in required_templates:
        if os.path.exists(template):
            print(f"  ✓ {template}")
        else:
            print(f"  ❌ {template} - NOT FOUND")
            all_exist = False
    
    return all_exist

def check_database():
    """Check if database tables exist"""
    print("\n🗄️ Checking Database Tables...")
    
    db_path = 'attendance.db'
    if not os.path.exists(db_path):
        print(f"  ⚠ Database not found at {db_path}")
        print("  Run 'python app.py' to create the database")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    required_tables = ['students', 'student_attendance']
    
    all_exist = True
    for table in required_tables:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        if cursor.fetchone():
            # Check row count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  ✓ {table} table exists ({count} records)")
        else:
            print(f"  ❌ {table} table - NOT FOUND")
            all_exist = False
    
    conn.close()
    return all_exist

def check_routes():
    """Check if routes are added to app.py"""
    print("\n🛣️ Checking Routes in app.py...")
    
    if not os.path.exists('app.py'):
        print("  ❌ app.py not found")
        return False
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_routes = [
        '/student/login',
        '/student/dashboard',
        '/student/attendance-history',
        '/student/profile',
        '/student/update-theme',
        '/student/logout',
        '/staff/mark-student-attendance'
    ]
    
    all_exist = True
    for route in required_routes:
        if route in content:
            print(f"  ✓ {route}")
        else:
            print(f"  ❌ {route} - NOT FOUND")
            all_exist = False
    
    return all_exist

def main():
    """Run all checks"""
    print("="*60)
    print("Student Portal Installation Verification")
    print("="*60)
    print()
    
    templates_ok = check_templates()
    database_ok = check_database()
    routes_ok = check_routes()
    
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    
    if templates_ok and database_ok and routes_ok:
        print("✅ All checks passed! Student portal is ready to use.")
        print("\n🚀 Next Steps:")
        print("  1. Run: python add_sample_students.py")
        print("  2. Start server: python app.py")
        print("  3. Open: http://localhost:5500/student/login")
    else:
        print("❌ Some checks failed. Please review the errors above.")
        
        if not templates_ok:
            print("\n  Templates issue: Make sure all HTML files are in templates/student/")
        
        if not database_ok:
            print("\n  Database issue: Run 'python app.py' to create tables")
        
        if not routes_ok:
            print("\n  Routes issue: Ensure student routes are added to app.py")

if __name__ == '__main__':
    main()
