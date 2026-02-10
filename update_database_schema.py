#!/usr/bin/env python3
"""
Script to update the database schema with salary fields
This adds the salary fields to existing staff table
"""

import sqlite3
import os
from app import app
from database import get_db

def update_staff_table_schema():
    """Add salary fields to existing staff table"""
    print("Updating staff table schema with salary fields...")
    
    with app.app_context():
        db = get_db()
        
        # List of salary fields to add
        salary_fields = [
            ('basic_salary', 'DECIMAL(10,2) DEFAULT 0.00'),
            ('hra', 'DECIMAL(10,2) DEFAULT 0.00'),
            ('transport_allowance', 'DECIMAL(10,2) DEFAULT 0.00'),
            ('other_allowances', 'DECIMAL(10,2) DEFAULT 0.00'),
            ('pf_deduction', 'DECIMAL(10,2) DEFAULT 0.00'),
            ('esi_deduction', 'DECIMAL(10,2) DEFAULT 0.00'),
            ('professional_tax', 'DECIMAL(10,2) DEFAULT 0.00'),
            ('other_deductions', 'DECIMAL(10,2) DEFAULT 0.00')
        ]
        
        # Check existing columns
        columns = db.execute("PRAGMA table_info(staff)").fetchall()
        existing_columns = [col['name'] for col in columns]
        
        print(f"Existing columns: {len(existing_columns)}")
        
        # Add missing salary fields
        added_fields = []
        for field_name, field_type in salary_fields:
            if field_name not in existing_columns:
                try:
                    db.execute(f"ALTER TABLE staff ADD COLUMN {field_name} {field_type}")
                    added_fields.append(field_name)
                    print(f"✅ Added field: {field_name}")
                except Exception as e:
                    print(f"❌ Failed to add field {field_name}: {e}")
        
        if added_fields:
            db.commit()
            print(f"\n✅ Successfully added {len(added_fields)} salary fields to staff table")
        else:
            print("\n✅ All salary fields already exist in staff table")
        
        # Verify the update
        columns_after = db.execute("PRAGMA table_info(staff)").fetchall()
        salary_columns = [col['name'] for col in columns_after if col['name'] in [f[0] for f in salary_fields]]
        
        print(f"\nSalary fields now in database: {len(salary_columns)}")
        for col in salary_columns:
            print(f"  - {col}")
        
        return len(salary_columns) == len(salary_fields)

if __name__ == '__main__':
    print("=" * 60)
    print("DATABASE SCHEMA UPDATE")
    print("=" * 60)
    
    try:
        success = update_staff_table_schema()
        
        if success:
            print("\n🎉 DATABASE SCHEMA UPDATE SUCCESSFUL! 🎉")
            print("✅ All salary fields are now available in the staff table")
            print("✅ The salary management system is ready to use")
        else:
            print("\n❌ DATABASE SCHEMA UPDATE INCOMPLETE")
            print("Some salary fields may be missing")
            
    except Exception as e:
        print(f"\n❌ DATABASE SCHEMA UPDATE FAILED: {e}")
        import traceback
        traceback.print_exc()
