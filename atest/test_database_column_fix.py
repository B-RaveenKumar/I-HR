#!/usr/bin/env python3
"""
Test script to verify the database column fix for allowances and deductions.
"""

import sqlite3
import sys
import os

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_database_schema():
    """Test the database schema to verify column names."""
    try:
        # Connect to database
        db = sqlite3.connect('vishnorex.db')
        cursor = db.cursor()
        
        # Get staff table schema
        cursor.execute("PRAGMA table_info(staff)")
        columns = cursor.fetchall()
        
        print("=== Staff Table Columns ===")
        column_names = []
        for col in columns:
            col_name = col[1]  # Column name is at index 1
            col_type = col[2]  # Column type is at index 2
            column_names.append(col_name)
            print(f"- {col_name}: {col_type}")
        
        # Check for allowances and deductions columns
        print("\n=== Column Analysis ===")
        
        allowance_columns = [col for col in column_names if 'allowance' in col.lower()]
        deduction_columns = [col for col in column_names if 'deduction' in col.lower()]
        
        print(f"Allowance columns: {allowance_columns}")
        print(f"Deduction columns: {deduction_columns}")
        
        # Check if the problematic columns exist
        has_allowances = 'allowances' in column_names
        has_deductions = 'deductions' in column_names
        
        print(f"\nColumn 'allowances' exists: {has_allowances}")
        print(f"Column 'deductions' exists: {has_deductions}")
        
        if not has_allowances and not has_deductions:
            print("✅ Confirmed: 'allowances' and 'deductions' columns do not exist")
            print("✅ The query needs to calculate totals from individual columns")
        
        # Test the corrected query structure
        print("\n=== Testing Corrected Query ===")
        test_query = '''
            SELECT id, staff_id, full_name, department, position,
                   basic_salary, 
                   (COALESCE(hra, 0) + COALESCE(transport_allowance, 0) + COALESCE(other_allowances, 0)) as allowances,
                   (COALESCE(pf_deduction, 0) + COALESCE(esi_deduction, 0) + COALESCE(professional_tax, 0) + COALESCE(other_deductions, 0)) as deductions,
                   COALESCE(basic_salary, 0) + (COALESCE(hra, 0) + COALESCE(transport_allowance, 0) + COALESCE(other_allowances, 0)) - (COALESCE(pf_deduction, 0) + COALESCE(esi_deduction, 0) + COALESCE(professional_tax, 0) + COALESCE(other_deductions, 0)) as net_salary
            FROM staff
            LIMIT 5
        '''
        
        try:
            cursor.execute(test_query)
            results = cursor.fetchall()
            print(f"✅ Query executed successfully! Found {len(results)} records")
            
            if results:
                print("\nSample result:")
                for i, row in enumerate(results[:1]):  # Show first result
                    print(f"  Staff ID: {row[1]}")
                    print(f"  Name: {row[2]}")
                    print(f"  Basic Salary: {row[5]}")
                    print(f"  Total Allowances: {row[6]}")
                    print(f"  Total Deductions: {row[7]}")
                    print(f"  Net Salary: {row[8]}")
                    
        except sqlite3.Error as e:
            print(f"❌ Query failed: {e}")
            return False
            
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_route_simulation():
    """Simulate the route call to test the fix."""
    print("\n=== Route Simulation Test ===")
    
    try:
        # Import Flask app components
        from app import app, get_db
        import json
        
        with app.app_context():
            # Simulate the generate_admin_report function logic
            db = get_db()
            school_id = 1  # Test with school_id 1
            department = None
            
            # Test the fixed query
            where_conditions = ['s.school_id = ?']
            params = [school_id]
            
            if department:
                where_conditions.append('s.department = ?')
                params.append(department)
            
            staff_query = f'''
                SELECT s.id, s.staff_id, s.full_name, s.department, s.position,
                       s.basic_salary, 
                       (COALESCE(s.hra, 0) + COALESCE(s.transport_allowance, 0) + COALESCE(s.other_allowances, 0)) as allowances,
                       (COALESCE(s.pf_deduction, 0) + COALESCE(s.esi_deduction, 0) + COALESCE(s.professional_tax, 0) + COALESCE(s.other_deductions, 0)) as deductions,
                       COALESCE(s.basic_salary, 0) + (COALESCE(s.hra, 0) + COALESCE(s.transport_allowance, 0) + COALESCE(s.other_allowances, 0)) - (COALESCE(s.pf_deduction, 0) + COALESCE(s.esi_deduction, 0) + COALESCE(s.professional_tax, 0) + COALESCE(s.other_deductions, 0)) as net_salary,
                       s.date_of_joining
                FROM staff s
                WHERE {' AND '.join(where_conditions)}
                ORDER BY s.department, s.full_name
            '''
            
            staff_data = db.execute(staff_query, params).fetchall()
            print(f"✅ Route simulation successful! Found {len(staff_data)} staff records")
            
            if staff_data:
                print("\nSample staff data:")
                for i, staff in enumerate(staff_data[:3]):  # Show first 3 records
                    print(f"  {i+1}. {staff['full_name']} - Department: {staff['department']}")
                    print(f"     Basic: {staff['basic_salary']}, Allowances: {staff['allowances']}, Deductions: {staff['deductions']}, Net: {staff['net_salary']}")
            
            return True
            
    except Exception as e:
        print(f"❌ Route simulation failed: {e}")
        return False

if __name__ == "__main__":
    print("Database Column Fix Verification")
    print("=" * 50)
    
    # Test database schema
    schema_ok = test_database_schema()
    
    # Test route simulation
    route_ok = test_route_simulation()
    
    print("\n" + "=" * 50)
    if schema_ok and route_ok:
        print("✅ ALL TESTS PASSED - Database column fix is working correctly!")
    else:
        print("❌ SOME TESTS FAILED - Please check the errors above")
    
    print("\nFix Summary:")
    print("- Changed query from 's.allowances' to calculated total allowances")
    print("- Changed query from 's.deductions' to calculated total deductions")
    print("- Query now uses actual database columns: hra, transport_allowance, other_allowances")
    print("- Query now uses actual database columns: pf_deduction, esi_deduction, professional_tax, other_deductions")
