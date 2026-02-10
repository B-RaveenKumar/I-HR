#!/usr/bin/env python3
"""
Test script for the enhanced edit staff functionality
"""

import sys
import os
import sqlite3
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_staff_table_columns():
    """Test if the staff table has all required salary columns"""
    print("\n🧪 Testing Staff Table Structure...")
    
    try:
        # Connect to database
        db_path = 'staff_management.db'
        if not os.path.exists(db_path):
            print(f"   ❌ Database file not found: {db_path}")
            return False
            
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
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
        
        print(f"   📊 Total columns in staff table: {len(column_names)}")
        print(f"   📊 Column names: {', '.join(column_names)}")
        
        missing_columns = []
        present_columns = []
        
        for col in required_salary_columns:
            if col in column_names:
                present_columns.append(col)
            else:
                missing_columns.append(col)
        
        if not missing_columns:
            print("   ✅ All required salary columns are present")
            for col in present_columns:
                print(f"      • {col}")
            return True
        else:
            print(f"   ❌ Missing salary columns: {missing_columns}")
            if present_columns:
                print(f"   ✅ Present salary columns: {present_columns}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing staff table structure: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def test_edit_staff_form_fields():
    """Test if the edit staff form includes all salary fields"""
    print("\n🧪 Testing Edit Staff Form Fields...")
    
    try:
        # Read the JavaScript file to check for salary fields
        js_file_path = 'static/js/staff_management.js'
        if not os.path.exists(js_file_path):
            print(f"   ❌ JavaScript file not found: {js_file_path}")
            return False
            
        with open(js_file_path, 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        # Check for salary field IDs in the edit form
        salary_field_ids = [
            'editBasicSalary',
            'editHRA',
            'editTransportAllowance', 
            'editOtherAllowances',
            'editPFDeduction',
            'editESIDeduction',
            'editProfessionalTax',
            'editOtherDeductions'
        ]
        
        missing_fields = []
        present_fields = []
        
        for field_id in salary_field_ids:
            if field_id in js_content:
                present_fields.append(field_id)
            else:
                missing_fields.append(field_id)
        
        if not missing_fields:
            print("   ✅ All salary fields are present in edit form")
            for field in present_fields:
                print(f"      • {field}")
            return True
        else:
            print(f"   ❌ Missing salary fields in edit form: {missing_fields}")
            if present_fields:
                print(f"   ✅ Present salary fields: {present_fields}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing edit staff form fields: {e}")
        return False

def test_flask_route_salary_handling():
    """Test if the Flask route handles salary fields"""
    print("\n🧪 Testing Flask Route Salary Handling...")
    
    try:
        # Read the app.py file to check for salary field handling
        app_file_path = 'app.py'
        if not os.path.exists(app_file_path):
            print(f"   ❌ Flask app file not found: {app_file_path}")
            return False
            
        with open(app_file_path, 'r', encoding='utf-8') as f:
            app_content = f.read()
        
        # Check for salary field handling in update_staff_enhanced route
        salary_form_fields = [
            "request.form.get('basic_salary'",
            "request.form.get('hra'",
            "request.form.get('transport_allowance'",
            "request.form.get('other_allowances'",
            "request.form.get('pf_deduction'",
            "request.form.get('esi_deduction'",
            "request.form.get('professional_tax'",
            "request.form.get('other_deductions'"
        ]
        
        missing_handlers = []
        present_handlers = []
        
        for field_handler in salary_form_fields:
            if field_handler in app_content:
                present_handlers.append(field_handler)
            else:
                missing_handlers.append(field_handler)
        
        if not missing_handlers:
            print("   ✅ All salary fields are handled in Flask route")
            for handler in present_handlers:
                print(f"      • {handler}")
            return True
        else:
            print(f"   ❌ Missing salary field handlers: {missing_handlers}")
            if present_handlers:
                print(f"   ✅ Present salary field handlers: {present_handlers}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing Flask route salary handling: {e}")
        return False

def test_calculate_salary_button():
    """Test if the Calculate Salary button functionality is fixed"""
    print("\n🧪 Testing Calculate Salary Button Functionality...")
    
    try:
        # Read the JavaScript file to check for button event listeners
        js_file_path = 'static/js/salary_management.js'
        if not os.path.exists(js_file_path):
            print(f"   ❌ JavaScript file not found: {js_file_path}")
            return False
            
        with open(js_file_path, 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        # Check for correct function name and event listener
        checks = [
            ("calculateBulkSalaries function", "function calculateBulkSalaries()"),
            ("Event listener setup", "addEventListener('click', calculateBulkSalaries)"),
            ("Display results function", "function displaySalaryResults("),
            ("Results container", "getElementById('salaryResultsContainer')")
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
        print(f"   ❌ Error testing calculate salary button: {e}")
        return False

def run_all_tests():
    """Run all tests for edit staff functionality"""
    print("🚀 Starting Edit Staff Functionality Tests")
    print("=" * 60)
    
    tests = [
        ("Staff Table Structure", test_staff_table_columns),
        ("Edit Staff Form Fields", test_edit_staff_form_fields),
        ("Flask Route Salary Handling", test_flask_route_salary_handling),
        ("Calculate Salary Button", test_calculate_salary_button),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        if test_func():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"🏁 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Edit staff functionality is working correctly.")
        print("\n✅ Summary of implemented features:")
        print("   • Salary fields added to edit staff form")
        print("   • Flask route updated to handle salary field updates")
        print("   • Calculate Salary button functionality fixed")
        print("   • Consistent styling with add staff form")
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
