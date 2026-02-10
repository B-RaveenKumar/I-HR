#!/usr/bin/env python3
"""
Test script to verify the staff address column fix.
"""

import sqlite3
import sys
import os

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_staff_query_fix():
    """Test the fixed staff directory query."""
    try:
        # Connect to database
        db = sqlite3.connect('vishnorex.db')
        db.row_factory = sqlite3.Row
        cursor = db.cursor()
        
        print("=== Testing Fixed Staff Directory Query ===")
        
        # Test the corrected query (should work now)
        fixed_query = '''
            SELECT s.staff_id, s.full_name, s.first_name, s.last_name,
                   s.date_of_birth, s.date_of_joining, s.department, s.position,
                   s.gender, s.phone, s.email, s.shift_type, s.basic_salary,
                   s.created_at
            FROM staff s
            WHERE s.school_id = ?
            ORDER BY s.department, s.full_name
            LIMIT 5
        '''
        
        try:
            cursor.execute(fixed_query, (1,))
            results = cursor.fetchall()
            print(f"✅ Fixed query executed successfully! Found {len(results)} records")
            
            if results:
                print("\nSample staff data:")
                for i, staff in enumerate(results[:3]):
                    print(f"  {i+1}. {staff['full_name']} - {staff['department']} - {staff['phone']}")
            
        except sqlite3.Error as e:
            print(f"❌ Fixed query failed: {e}")
            return False
        
        # Test the old problematic query (should fail)
        print("\n=== Testing Old Problematic Query (Expected to Fail) ===")
        old_query = '''
            SELECT s.staff_id, s.full_name, s.address, s.emergency_contact,
                   s.qualification, s.experience, s.updated_at
            FROM staff s
            WHERE s.school_id = ?
            LIMIT 1
        '''
        
        try:
            cursor.execute(old_query, (1,))
            results = cursor.fetchall()
            print(f"❌ Old query unexpectedly succeeded! This should not happen.")
            return False
        except sqlite3.Error as e:
            print(f"✅ Old query correctly failed: {e}")
            print("   This confirms the missing columns are properly identified.")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_route_simulation():
    """Simulate the staff directory report generation."""
    print("\n=== Route Simulation Test ===")
    
    try:
        # Import Flask app components
        from app import app, get_db
        
        with app.app_context():
            db = get_db()
            school_id = 1  # Test with school_id 1
            
            # Test the fixed staff directory query
            staff_data = db.execute('''
                SELECT s.staff_id, s.full_name, s.first_name, s.last_name,
                       s.date_of_birth, s.date_of_joining, s.department, s.position,
                       s.gender, s.phone, s.email, s.shift_type, s.basic_salary,
                       s.created_at
                FROM staff s
                WHERE s.school_id = ?
                ORDER BY s.department, s.full_name
            ''', (school_id,)).fetchall()
            
            print(f"✅ Staff directory query simulation successful! Found {len(staff_data)} staff records")
            
            if staff_data:
                print("\nSample staff data (available columns):")
                for i, staff in enumerate(staff_data[:2]):
                    print(f"  {i+1}. Staff ID: {staff['staff_id']}")
                    print(f"     Name: {staff['full_name']}")
                    print(f"     Department: {staff['department']}")
                    print(f"     Email: {staff['email']}")
                    print(f"     Phone: {staff['phone']}")
                    print(f"     Shift: {staff['shift_type']}")
            
            return True
            
    except Exception as e:
        print(f"❌ Route simulation failed: {e}")
        return False

def test_column_availability():
    """Test which staff columns are actually available."""
    print("\n=== Column Availability Test ===")
    
    try:
        db = sqlite3.connect('vishnorex.db')
        cursor = db.cursor()
        
        # Get staff table schema
        cursor.execute("PRAGMA table_info(staff)")
        columns = cursor.fetchall()
        
        available_columns = [col[1] for col in columns]
        
        # Check specific columns that reports might need
        report_columns = [
            'staff_id', 'full_name', 'first_name', 'last_name',
            'date_of_birth', 'date_of_joining', 'department', 'position',
            'gender', 'phone', 'email', 'shift_type', 'basic_salary',
            'created_at'
        ]
        
        print("Staff report column availability:")
        all_available = True
        for col in report_columns:
            if col in available_columns:
                print(f"  ✅ {col}")
            else:
                print(f"  ❌ {col} - MISSING!")
                all_available = False
        
        if all_available:
            print("\n✅ All required columns for staff reports are available!")
        else:
            print("\n❌ Some required columns are missing!")
            
        db.close()
        return all_available
        
    except Exception as e:
        print(f"❌ Column availability test failed: {e}")
        return False

if __name__ == "__main__":
    print("Staff Address Column Fix Verification")
    print("=" * 60)
    
    # Test database queries
    query_ok = test_staff_query_fix()
    
    # Test route simulation
    route_ok = test_route_simulation()
    
    # Test column availability
    columns_ok = test_column_availability()
    
    print("\n" + "=" * 60)
    if query_ok and route_ok and columns_ok:
        print("✅ ALL TESTS PASSED - Staff address column fix is working correctly!")
    else:
        print("❌ SOME TESTS FAILED - Please check the errors above")
    
    print("\nFix Summary:")
    print("- Removed non-existent columns from staff directory query:")
    print("  • s.address (not in staff table)")
    print("  • s.emergency_contact (not in staff table)")
    print("  • s.qualification (not in staff table)")
    print("  • s.experience (not in staff table)")
    print("  • s.updated_at (not in staff table)")
    print("- Updated Excel report headers and data cells to match")
    print("- Reduced column count from 15 to 11 columns")
    print("- Fixed column width adjustment and cell ranges")
    
    print("\nStaff directory report now includes:")
    print("  1. S.No, 2. Staff ID, 3. Full Name, 4. Department, 5. Position")
    print("  6. Gender, 7. Phone, 8. Email, 9. Date of Joining, 10. Date of Birth, 11. Shift Type")
