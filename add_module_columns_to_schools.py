"""
Add module settings columns to schools table
No separate database - just adds columns to existing schools table
Works with both MySQL and SQLite
"""
import os
import sys

# Check if using MySQL
DATABASE_URL = os.getenv('DATABASE_URL', 'mysql+pymysql://root:Vish0803@mysql-env-94i0cda6di.ap-south-1a.lb.nimbuz.tech:32261/ihrdb')
USE_MYSQL = DATABASE_URL.startswith('mysql')

def add_module_columns():
    if USE_MYSQL:
        # Use MySQL
        import pymysql
        import re
        
        # Parse MySQL URL
        url = re.sub(r'^mysql\+pymysql://', '', DATABASE_URL)
        m = re.match(
            r'(?P<user>[^:]+):(?P<password>[^@]*)@(?P<host>[^:/]+)(?::(?P<port>\d+))?/(?P<db>.+)',
            url
        )
        if not m:
            print("❌ Cannot parse DATABASE_URL")
            return
        
        conn = pymysql.connect(
            user=m.group('user'),
            password=m.group('password'),
            host=m.group('host'),
            port=int(m.group('port') or 3306),
            database=m.group('db'),
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        print("✅ Connected to MySQL database")
    else:
        # Use SQLite
        import sqlite3
        db_path = os.path.join(os.path.dirname(__file__), 'instance', 'vishnorex.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print("✅ Connected to SQLite database")
    
    # List of module columns to add
    modules = [
        'staff_management_enabled',
        'shift_management_enabled', 
        'salary_management_enabled',
        'timetable_management_enabled',
        'reports_enabled',
        'biometric_devices_enabled',
        'department_shift_assignments_enabled',
        'holiday_management_enabled',
        'quota_management_enabled',
        'sub_admin_management_enabled'
    ]
    
    # Add each column (TINYINT for MySQL, INTEGER for SQLite, DEFAULT 1 = enabled)
    for module in modules:
        try:
            if USE_MYSQL:
                cursor.execute(f'ALTER TABLE schools ADD COLUMN {module} TINYINT DEFAULT 1')
            else:
                cursor.execute(f'ALTER TABLE schools ADD COLUMN {module} INTEGER DEFAULT 1')
            print(f"✅ Added column: {module}")
        except Exception as e:
            error_msg = str(e).lower()
            if 'duplicate column' in error_msg or "duplicate" in error_msg:
                print(f"⚠️  Column {module} already exists, skipping...")
            else:
                print(f"❌ Error adding {module}: {e}")
    
    conn.commit()
    conn.close()
    
    print("\n✨ Module columns added to schools table successfully!")
    print("📝 All modules are enabled by default (value = 1)")

if __name__ == '__main__':
    add_module_columns()
