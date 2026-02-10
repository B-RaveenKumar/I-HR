#!/usr/bin/env python3
"""
Check existing database schema and create missing tables for quota management
"""

from app import app
from database import get_db, init_db
import sqlite3

def check_existing_schema():
    """Check what tables currently exist in the database"""
    try:
        init_db(app)
        with app.app_context():
            db = get_db()
            cursor = db.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = cursor.fetchall()
            
            print("Existing tables:")
            for table in tables:
                print(f"  - {table[0]}")
                
                # Get column info for each table
                cursor.execute(f"PRAGMA table_info({table[0]})")
                columns = cursor.fetchall()
                for col in columns:
                    print(f"    {col[1]} ({col[2]})")
                print()
            
            return True
            
    except Exception as e:
        print(f'Error checking schema: {e}')
        return False

def create_missing_tables():
    """Create missing tables for quota management"""
    try:
        with app.app_context():
            db = get_db()
            cursor = db.cursor()
            
            # Create quota_types table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quota_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    unit TEXT NOT NULL DEFAULT 'Days',
                    default_value INTEGER NOT NULL DEFAULT 0,
                    school_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (school_id) REFERENCES schools (id)
                )
            """)
            print("✓ Created quota_types table")
            
            # Create staff_quotas table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS staff_quotas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    staff_id INTEGER NOT NULL,
                    quota_type_id INTEGER NOT NULL,
                    year INTEGER NOT NULL,
                    allocated_quota INTEGER NOT NULL DEFAULT 0,
                    used_quota INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (staff_id) REFERENCES staff (id),
                    FOREIGN KEY (quota_type_id) REFERENCES quota_types (id),
                    UNIQUE (staff_id, quota_type_id, year)
                )
            """)
            print("✓ Created staff_quotas table")
            
            # Create od_applications table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS od_applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    staff_id INTEGER NOT NULL,
                    school_id INTEGER NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    days_requested INTEGER NOT NULL,
                    reason TEXT,
                    status TEXT DEFAULT 'pending',
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    approved_at TIMESTAMP,
                    approved_by INTEGER,
                    FOREIGN KEY (staff_id) REFERENCES staff (id),
                    FOREIGN KEY (school_id) REFERENCES schools (id)
                )
            """)
            print("✓ Created od_applications table")
            
            # Insert default quota types
            cursor.execute("SELECT id FROM schools LIMIT 1")
            school_result = cursor.fetchone()
            if school_result:
                school_id = school_result[0]
                
                default_quotas = [
                    ('CL', 'Days', 12),
                    ('SL', 'Days', 10),
                    ('EL', 'Days', 21),
                    ('ML', 'Days', 90),
                    ('PL', 'Days', 7),
                    ('Permission', 'Hours', 40),
                    ('On Duty', 'Days', 20)
                ]
                
                for name, unit, default_value in default_quotas:
                    cursor.execute("""
                        INSERT OR IGNORE INTO quota_types (name, unit, default_value, school_id)
                        VALUES (?, ?, ?, ?)
                    """, (name, unit, default_value, school_id))
                
                print(f"✓ Inserted default quota types for school {school_id}")
            
            db.commit()
            print("\n✓ All missing tables created successfully!")
            return True
            
    except Exception as e:
        print(f'Error creating tables: {e}')
        return False

if __name__ == '__main__':
    print("Checking and creating database schema...\n")
    
    # Check existing schema
    check_existing_schema()
    
    print("\n" + "="*50)
    print("Creating missing tables...\n")
    
    # Create missing tables
    create_missing_tables()
    
    print("\nSchema setup completed!")