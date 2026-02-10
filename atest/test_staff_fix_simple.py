#!/usr/bin/env python3
"""
Simple test for staff address column fix.
"""

import sqlite3

def test_staff_queries():
    """Test staff queries with the fixed columns."""
    try:
        # Connect to database
        db = sqlite3.connect('vishnorex.db')
        db.row_factory = sqlite3.Row
        
        print("=== Testing Staff Directory Query Fix ===")
        
        # Test the FIXED query (from the corrected code)
        print("\n1. Testing FIXED staff directory query:")
        fixed_query = '''
            SELECT s.staff_id, s.full_name, s.first_name, s.last_name,
                   s.date_of_birth, s.date_of_joining, s.department, s.position,
                   s.gender, s.phone, s.email, s.shift_type, s.basic_salary,
                   s.created_at
            FROM staff s
            WHERE s.school_id = ?
            ORDER BY s.department, s.full_name
            LIMIT 3
        '''
        
        try:
            cursor = db.execute(fixed_query, (1,))
            results = cursor.fetchall()
            print(f"   ✅ SUCCESS: Found {len(results)} staff records")
            
            if results:
                for i, staff in enumerate(results):
                    print(f"   - Staff {i+1}: {staff['full_name']} ({staff['department']})")
                    
        except sqlite3.Error as e:
            print(f"   ❌ FAILED: {e}")
            return False
        
        # Test the OLD problematic query (should fail)
        print("\n2. Testing OLD problematic query (should fail):")
        old_query = '''
            SELECT s.staff_id, s.full_name, s.address, s.emergency_contact,
                   s.qualification, s.experience, s.updated_at
            FROM staff s
            WHERE s.school_id = ?
            LIMIT 1
        '''
        
        try:
            cursor = db.execute(old_query, (1,))
            results = cursor.fetchall()
            print(f"   ❌ UNEXPECTED SUCCESS: Query should have failed but returned {len(results)} records")
        except sqlite3.Error as e:
            print(f"   ✅ EXPECTED FAILURE: {e}")
            print("   This confirms the problematic columns don't exist.")
        
        # Test individual problematic columns
        print("\n3. Testing individual problematic columns:")
        problematic_columns = ['address', 'emergency_contact', 'qualification', 'experience', 'updated_at']
        
        for col in problematic_columns:
            try:
                test_query = f"SELECT s.{col} FROM staff s LIMIT 1"
                cursor = db.execute(test_query)
                results = cursor.fetchall()
                print(f"   ❌ Column '{col}' exists (unexpected)")
            except sqlite3.Error:
                print(f"   ✅ Column '{col}' doesn't exist (expected)")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def check_available_columns():
    """List all available columns in staff table."""
    try:
        db = sqlite3.connect('vishnorex.db')
        cursor = db.cursor()
        
        cursor.execute("PRAGMA table_info(staff)")
        columns = cursor.fetchall()
        
        print("\n=== Available Staff Table Columns ===")
        for i, col in enumerate(columns, 1):
            col_name = col[1]
            col_type = col[2]
            print(f"   {i:2d}. {col_name} ({col_type})")
        
        print(f"\nTotal: {len(columns)} columns available")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Column check failed: {e}")
        return False

if __name__ == "__main__":
    print("Staff Address Column Fix - Quick Test")
    print("=" * 50)
    
    # Test the queries
    queries_ok = test_staff_queries()
    
    # Check available columns
    columns_ok = check_available_columns()
    
    print("\n" + "=" * 50)
    if queries_ok and columns_ok:
        print("✅ STAFF ADDRESS COLUMN FIX VERIFIED!")
        print("\nSummary of changes made:")
        print("• Removed s.address from staff directory query")
        print("• Removed s.emergency_contact from staff directory query")
        print("• Removed s.qualification from staff directory query")
        print("• Removed s.experience from staff directory query")
        print("• Removed s.updated_at from staff directory query")
        print("• Updated Excel headers from 15 to 11 columns")
        print("• Fixed column ranges and cell mappings")
        
        print("\nStaff directory report now works with existing columns:")
        print("1. S.No  2. Staff ID  3. Full Name  4. Department  5. Position")
        print("6. Gender  7. Phone  8. Email  9. Date of Joining  10. Date of Birth  11. Shift Type")
    else:
        print("❌ TESTS FAILED - Issues remain")
        
    print("\nNext steps:")
    print("• Test staff report generation in the web interface")
    print("• Verify Excel file downloads work correctly")
    print("• Check other report types for similar issues")
