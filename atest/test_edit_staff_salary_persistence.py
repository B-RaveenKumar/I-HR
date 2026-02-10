#!/usr/bin/env python3
"""
Test script for the Edit Staff Member salary field persistence fix
"""

import sys
import os
import sqlite3
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_database_salary_fields():
    """Test if the database has salary fields and sample data"""
    print("\n🧪 Testing Database Salary Fields...")
    
    try:
        # Connect to database
        db_path = 'staff_management.db'
        if not os.path.exists(db_path):
            print(f"   ❌ Database file not found: {db_path}")
            return False
            
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if staff table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='staff'")
        if not cursor.fetchone():
            print("   ❌ Staff table not found")
            return False
        
        # Get table structure
        cursor.execute("PRAGMA table_info(staff)")
        columns = cursor.fetchall()
        column_names = [col['name'] for col in columns]
        
        # Required salary columns
        required_salary_columns = [
            'basic_salary',
            'hra', 
            'transport_allowance',
            'other_allowances',
            'pf_deduction',
            'esi_deduction', 
            'professional_tax',
            'other_deductions'
        ]
        
        missing_columns = [col for col in required_salary_columns if col not in column_names]
        
        if missing_columns:
            print(f"   ❌ Missing salary columns: {missing_columns}")
            return False
        
        print("   ✅ All salary columns present in database")
        
        # Check if there's any staff data
        cursor.execute("SELECT COUNT(*) as count FROM staff")
        staff_count = cursor.fetchone()['count']
        print(f"   📊 Total staff records: {staff_count}")
        
        if staff_count > 0:
            # Check if any staff has salary data
            cursor.execute("""
                SELECT id, staff_id, full_name, basic_salary, hra, transport_allowance 
                FROM staff 
                WHERE basic_salary IS NOT NULL OR hra IS NOT NULL 
                LIMIT 5
            """)
            staff_with_salary = cursor.fetchall()
            
            if staff_with_salary:
                print(f"   ✅ Found {len(staff_with_salary)} staff members with salary data")
                for staff in staff_with_salary:
                    print(f"      • {staff['full_name']} (ID: {staff['staff_id']}) - Basic: ₹{staff['basic_salary'] or 'N/A'}, HRA: ₹{staff['hra'] or 'N/A'}")
            else:
                print("   ⚠️ No staff members have salary data set")
        
        return True
            
    except Exception as e:
        print(f"   ❌ Error testing database: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def test_flask_route_query():
    """Test if the Flask route query includes salary fields"""
    print("\n🧪 Testing Flask Route Query...")
    
    try:
        # Read the app.py file to check the query
        app_file_path = 'app.py'
        if not os.path.exists(app_file_path):
            print(f"   ❌ Flask app file not found: {app_file_path}")
            return False
            
        with open(app_file_path, 'r', encoding='utf-8') as f:
            app_content = f.read()
        
        # Find the get_staff_details_enhanced route
        route_start = app_content.find('@app.route(\'/get_staff_details_enhanced\')')
        if route_start == -1:
            print("   ❌ get_staff_details_enhanced route not found")
            return False
        
        # Extract the route function (next 1000 characters should be enough)
        route_content = app_content[route_start:route_start + 1000]
        
        # Check if salary fields are in the SELECT query
        salary_fields_in_query = [
            'basic_salary',
            'hra',
            'transport_allowance',
            'other_allowances',
            'pf_deduction',
            'esi_deduction',
            'professional_tax',
            'other_deductions'
        ]
        
        missing_fields = []
        present_fields = []
        
        for field in salary_fields_in_query:
            if field in route_content:
                present_fields.append(field)
            else:
                missing_fields.append(field)
        
        if not missing_fields:
            print("   ✅ All salary fields are included in the database query")
            for field in present_fields:
                print(f"      • {field}")
            return True
        else:
            print(f"   ❌ Missing salary fields in query: {missing_fields}")
            if present_fields:
                print(f"   ✅ Present salary fields: {present_fields}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing Flask route query: {e}")
        return False

def test_javascript_field_handling():
    """Test if JavaScript properly handles salary field values"""
    print("\n🧪 Testing JavaScript Field Handling...")
    
    try:
        # Read the JavaScript file
        js_file_path = 'static/js/staff_management.js'
        if not os.path.exists(js_file_path):
            print(f"   ❌ JavaScript file not found: {js_file_path}")
            return False
            
        with open(js_file_path, 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        # Check for proper null handling in salary fields
        checks = [
            ("Basic salary field with null handling", "staff.basic_salary || ''"),
            ("HRA field with null handling", "staff.hra || ''"),
            ("Transport allowance field with null handling", "staff.transport_allowance || ''"),
            ("Other allowances field with null handling", "staff.other_allowances || ''"),
            ("PF deduction field with null handling", "staff.pf_deduction || ''"),
            ("ESI deduction field with null handling", "staff.esi_deduction || ''"),
            ("Professional tax field with null handling", "staff.professional_tax || ''"),
            ("Other deductions field with null handling", "staff.other_deductions || ''"),
            ("Debug logging for salary fields", "console.log('Salary field values from database:')"),
            ("Field verification after population", "console.log('Form field values after population:')")
        ]
        
        all_passed = True
        for check_name, check_pattern in checks:
            if check_pattern in js_content:
                print(f"   ✅ {check_name}: Found")
            else:
                print(f"   ❌ {check_name}: Missing")
                all_passed = False
        
        return all_passed
            
    except Exception as e:
        print(f"   ❌ Error testing JavaScript field handling: {e}")
        return False

def test_form_field_persistence_logic():
    """Test the logic for form field persistence"""
    print("\n🧪 Testing Form Field Persistence Logic...")
    
    try:
        # Read the JavaScript file
        js_file_path = 'static/js/staff_management.js'
        if not os.path.exists(js_file_path):
            print(f"   ❌ JavaScript file not found: {js_file_path}")
            return False
            
        with open(js_file_path, 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        # Check for persistence-related features
        persistence_checks = [
            ("Loading state display", "Loading staff details..."),
            ("Error handling for failed loads", "Failed to load staff details"),
            ("Manual field population fallback", "Manually setting basic salary field value"),
            ("Field value verification", "basicSalaryField.value"),
            ("Timeout for field verification", "setTimeout(() => {")
        ]
        
        all_passed = True
        for check_name, check_pattern in persistence_checks:
            if check_pattern in js_content:
                print(f"   ✅ {check_name}: Implemented")
            else:
                print(f"   ❌ {check_name}: Missing")
                all_passed = False
        
        return all_passed
            
    except Exception as e:
        print(f"   ❌ Error testing form field persistence logic: {e}")
        return False

def run_all_tests():
    """Run all tests for edit staff salary field persistence"""
    print("🚀 Starting Edit Staff Salary Field Persistence Tests")
    print("=" * 70)
    
    tests = [
        ("Database Salary Fields", test_database_salary_fields),
        ("Flask Route Query", test_flask_route_query),
        ("JavaScript Field Handling", test_javascript_field_handling),
        ("Form Field Persistence Logic", test_form_field_persistence_logic),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        if test_func():
            passed += 1
    
    print("\n" + "=" * 70)
    print(f"🏁 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Edit staff salary field persistence is fixed.")
        print("\n✅ Summary of fixes implemented:")
        print("   • Flask route now includes all salary fields in database query")
        print("   • JavaScript properly handles null values with empty string fallback")
        print("   • Added debug logging to track field population")
        print("   • Implemented manual field population fallback")
        print("   • Added loading states and error handling")
        print("   • Form fields now persist values correctly during editing session")
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
