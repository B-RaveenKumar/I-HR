#!/usr/bin/env python3
"""
Check the actual staff table schema to identify missing columns.
"""

import sqlite3
import sys
import os

def check_staff_table_schema():
    """Check the actual staff table schema in the database."""
    try:
        # Connect to database
        db = sqlite3.connect('vishnorex.db')
        cursor = db.cursor()
        
        # Get staff table schema
        cursor.execute("PRAGMA table_info(staff)")
        columns = cursor.fetchall()
        
        print("=== Current Staff Table Schema ===")
        print("Column Name | Type | Not Null | Default | Primary Key")
        print("-" * 60)
        
        column_names = []
        for col in columns:
            col_id, name, data_type, not_null, default_val, pk = col
            column_names.append(name)
            print(f"{name:<15} | {data_type:<10} | {not_null:<8} | {default_val or 'NULL':<7} | {pk}")
        
        print(f"\nTotal columns: {len(column_names)}")
        
        # Check for address-related columns
        print("\n=== Address-Related Column Analysis ===")
        address_columns = [col for col in column_names if 'address' in col.lower()]
        if address_columns:
            print(f"Found address columns: {address_columns}")
        else:
            print("❌ No address columns found in staff table")
        
        # Check for other missing columns mentioned in the query
        print("\n=== Missing Column Analysis ===")
        query_columns = [
            'address', 'emergency_contact', 'qualification', 'experience', 'updated_at'
        ]
        
        missing_columns = []
        for col in query_columns:
            if col not in column_names:
                missing_columns.append(col)
                print(f"❌ Missing column: {col}")
            else:
                print(f"✅ Found column: {col}")
        
        # Show existing columns that might be alternatives
        print("\n=== Available Columns for Reference ===")
        for col in sorted(column_names):
            print(f"  - {col}")
            
        db.close()
        return missing_columns
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return []

def suggest_fixes(missing_columns):
    """Suggest fixes for missing columns."""
    print("\n=== Suggested Fixes ===")
    
    if missing_columns:
        print("Option 1: Remove missing columns from queries")
        print("Option 2: Add missing columns to database schema")
        print("Option 3: Use NULL or default values for missing columns")
        
        for col in missing_columns:
            if col == 'address':
                print(f"  - {col}: Could be added as TEXT field for staff home address")
            elif col == 'emergency_contact':
                print(f"  - {col}: Could be added as TEXT field for emergency contact info")
            elif col == 'qualification':
                print(f"  - {col}: Could be added as TEXT field for educational qualifications")
            elif col == 'experience':
                print(f"  - {col}: Could be added as TEXT or INTEGER field for work experience")
            elif col == 'updated_at':
                print(f"  - {col}: Could be added as TIMESTAMP field with DEFAULT CURRENT_TIMESTAMP")
    else:
        print("✅ No missing columns detected")

if __name__ == "__main__":
    print("Staff Table Schema Analysis")
    print("=" * 50)
    
    missing_columns = check_staff_table_schema()
    suggest_fixes(missing_columns)
    
    print("\n" + "=" * 50)
    print("Next Steps:")
    print("1. Update SQL queries to remove missing column references")
    print("2. Or add missing columns to database schema")
    print("3. Test report generation after fixes")
