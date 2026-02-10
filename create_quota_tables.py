#!/usr/bin/env python3
"""
Database Schema Update: Leave, OD & Permission Quota System
==========================================================

This script creates the necessary tables for the quota management system:
- staff_leave_quotas: Stores leave quotas by type and year
- staff_od_quotas: Stores on-duty quotas by year  
- staff_permission_quotas: Stores permission quotas by year

The system tracks quotas annually and allows for flexible quota assignment.
"""

import sqlite3
import os
from app import app
from database import get_db

def create_quota_tables():
    """Create quota management tables"""
    print("Creating quota management tables...")
    
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        try:
            # Create staff_leave_quotas table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS staff_leave_quotas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                staff_id INTEGER NOT NULL,
                school_id INTEGER NOT NULL,
                quota_year INTEGER NOT NULL,
                leave_type TEXT NOT NULL CHECK(leave_type IN ('CL', 'SL', 'EL', 'ML')),
                allocated_days INTEGER NOT NULL DEFAULT 0,
                used_days INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE CASCADE,
                FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE,
                UNIQUE(staff_id, school_id, quota_year, leave_type)
            )
            ''')
            print("✅ Created staff_leave_quotas table")
            
            # Create staff_od_quotas table  
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS staff_od_quotas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                staff_id INTEGER NOT NULL,
                school_id INTEGER NOT NULL,
                quota_year INTEGER NOT NULL,
                allocated_days INTEGER NOT NULL DEFAULT 0,
                used_days INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE CASCADE,
                FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE,
                UNIQUE(staff_id, school_id, quota_year)
            )
            ''')
            print("✅ Created staff_od_quotas table")
            
            # Create staff_permission_quotas table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS staff_permission_quotas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                staff_id INTEGER NOT NULL,
                school_id INTEGER NOT NULL,
                quota_year INTEGER NOT NULL,
                allocated_hours DECIMAL(5,2) NOT NULL DEFAULT 0.00,
                used_hours DECIMAL(5,2) NOT NULL DEFAULT 0.00,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE CASCADE,
                FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE,
                UNIQUE(staff_id, school_id, quota_year)
            )
            ''')
            print("✅ Created staff_permission_quotas table")
            
            # Create quota_usage_log table for audit trail
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS quota_usage_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                staff_id INTEGER NOT NULL,
                school_id INTEGER NOT NULL,
                quota_type TEXT NOT NULL CHECK(quota_type IN ('leave', 'od', 'permission')),
                leave_type TEXT, -- Only for leave quotas
                application_id INTEGER NOT NULL,
                days_used INTEGER DEFAULT 0,
                hours_used DECIMAL(5,2) DEFAULT 0.00,
                action_type TEXT NOT NULL CHECK(action_type IN ('used', 'restored')),
                action_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_by INTEGER,
                notes TEXT,
                FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE CASCADE,
                FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE
            )
            ''')
            print("✅ Created quota_usage_log table")
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_leave_quotas_staff_year ON staff_leave_quotas(staff_id, quota_year)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_od_quotas_staff_year ON staff_od_quotas(staff_id, quota_year)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_permission_quotas_staff_year ON staff_permission_quotas(staff_id, quota_year)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_quota_usage_staff ON quota_usage_log(staff_id, quota_type)')
            print("✅ Created performance indexes")
            
            db.commit()
            return True
            
        except Exception as e:
            print(f"❌ Error creating quota tables: {e}")
            db.rollback()
            return False

def create_default_quota_config_table():
    """Create default quota configuration table for institution-wide defaults"""
    print("Creating default quota configuration table...")
    
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        try:
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS default_quota_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                school_id INTEGER NOT NULL,
                leave_type TEXT, -- NULL for OD and Permission defaults
                quota_type TEXT NOT NULL CHECK(quota_type IN ('leave', 'od', 'permission')),
                default_allocation INTEGER DEFAULT 0, -- Days for leave/OD, Hours for permission
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE,
                UNIQUE(school_id, quota_type, leave_type)
            )
            ''')
            print("✅ Created default_quota_config table")
            
            db.commit()
            return True
            
        except Exception as e:
            print(f"❌ Error creating default quota config table: {e}")
            db.rollback()
            return False

def insert_sample_default_quotas():
    """Insert sample default quota configurations"""
    print("Inserting sample default quota configurations...")
    
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        try:
            # Get first school ID for sample data
            school = cursor.execute('SELECT id FROM schools LIMIT 1').fetchone()
            if not school:
                print("⚠️  No schools found - skipping sample data")
                return True
                
            school_id = school[0]
            
            # Check if defaults already exist
            existing = cursor.execute(
                'SELECT COUNT(*) as count FROM default_quota_config WHERE school_id = ?',
                (school_id,)
            ).fetchone()
            
            if existing and existing[0] > 0:
                print("ℹ️  Default quotas already exist - skipping")
                return True
            
            # Insert default leave quotas
            leave_defaults = [
                ('CL', 12),  # Casual Leave: 12 days
                ('SL', 7),   # Sick Leave: 7 days  
                ('EL', 21),  # Earned Leave: 21 days
                ('ML', 180)  # Maternity Leave: 180 days
            ]
            
            for leave_type, days in leave_defaults:
                cursor.execute('''
                    INSERT INTO default_quota_config 
                    (school_id, quota_type, leave_type, default_allocation)
                    VALUES (?, 'leave', ?, ?)
                ''', (school_id, leave_type, days))
            
            # Insert default OD quota
            cursor.execute('''
                INSERT INTO default_quota_config 
                (school_id, quota_type, leave_type, default_allocation)
                VALUES (?, 'od', NULL, ?)
            ''', (school_id, 10))  # 10 OD days per year
            
            # Insert default Permission quota  
            cursor.execute('''
                INSERT INTO default_quota_config 
                (school_id, quota_type, leave_type, default_allocation)
                VALUES (?, 'permission', NULL, ?)
            ''', (school_id, 15))  # 15 permission hours per year
            
            db.commit()
            print("✅ Inserted sample default quota configurations")
            return True
            
        except Exception as e:
            print(f"❌ Error inserting sample defaults: {e}")
            db.rollback()
            return False

def verify_quota_tables():
    """Verify that all quota tables were created successfully"""
    print("Verifying quota tables...")
    
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        required_tables = [
            'staff_leave_quotas',
            'staff_od_quotas', 
            'staff_permission_quotas',
            'quota_usage_log',
            'default_quota_config'
        ]
        
        try:
            for table_name in required_tables:
                cursor.execute('''
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name = ?
                ''', (table_name,))
                
                if cursor.fetchone():
                    print(f"✅ Table {table_name} exists")
                else:
                    print(f"❌ Table {table_name} missing")
                    return False
            
            # Check table structures
            print("\n📊 Table Structure Verification:")
            
            # Verify staff_leave_quotas structure
            cursor.execute('PRAGMA table_info(staff_leave_quotas)')
            leave_columns = [col[1] for col in cursor.fetchall()]
            expected_leave_cols = ['id', 'staff_id', 'school_id', 'quota_year', 'leave_type', 'allocated_days', 'used_days']
            
            for col in expected_leave_cols:
                if col in leave_columns:
                    print(f"  ✅ staff_leave_quotas.{col}")
                else:
                    print(f"  ❌ staff_leave_quotas.{col} missing")
                    return False
            
            print("✅ All quota tables verified successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error verifying tables: {e}")
            return False

def main():
    """Main execution function"""
    print("=" * 70)
    print("QUOTA MANAGEMENT SYSTEM - DATABASE SETUP")
    print("=" * 70)
    
    try:
        # Step 1: Create quota tables
        if not create_quota_tables():
            print("❌ Failed to create quota tables")
            return 1
        
        # Step 2: Create default config table
        if not create_default_quota_config_table():
            print("❌ Failed to create default quota config table")
            return 1
        
        # Step 3: Insert sample defaults
        if not insert_sample_default_quotas():
            print("❌ Failed to insert sample defaults")
            return 1
        
        # Step 4: Verify everything
        if not verify_quota_tables():
            print("❌ Table verification failed")
            return 1
        
        print("\n🎉 QUOTA SYSTEM DATABASE SETUP COMPLETE! 🎉")
        print("✅ All quota management tables created successfully")
        print("✅ Default quota configurations added")
        print("✅ Database indexes created for performance")
        print("✅ System ready for quota management implementation")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ SETUP FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())