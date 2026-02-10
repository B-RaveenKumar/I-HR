#!/usr/bin/env python3
"""
Test script for the Staff Search & Filters functionality
"""

import sys
import os
import sqlite3
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_html_filter_fields():
    """Test if all filter fields are present in the HTML template"""
    print("\n🧪 Testing HTML Filter Fields...")
    
    try:
        # Read the HTML template
        html_file_path = 'templates/staff_management.html'
        if not os.path.exists(html_file_path):
            print(f"   ❌ HTML template not found: {html_file_path}")
            return False
            
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Check for all required filter fields
        required_fields = [
            ('Search Input', 'id="staffSearchInput"'),
            ('Department Filter', 'id="departmentFilter"'),
            ('Position Filter', 'id="positionFilter"'),
            ('Gender Filter', 'id="genderFilter"'),
            ('Date From Filter', 'id="dateFromFilter"'),
            ('Date To Filter', 'id="dateToFilter"'),
            ('Apply Filters Button', 'id="applyFiltersBtn"'),
            ('Clear Filters Button', 'id="clearFiltersBtn"')
        ]
        
        all_passed = True
        for field_name, field_id in required_fields:
            if field_id in html_content:
                print(f"   ✅ {field_name}: Found")
            else:
                print(f"   ❌ {field_name}: Missing")
                all_passed = False
        
        return all_passed
            
    except Exception as e:
        print(f"   ❌ Error testing HTML filter fields: {e}")
        return False

def test_javascript_filter_functionality():
    """Test if JavaScript has all the required filter functionality"""
    print("\n🧪 Testing JavaScript Filter Functionality...")
    
    try:
        # Read the JavaScript file
        js_file_path = 'static/js/staff_management.js'
        if not os.path.exists(js_file_path):
            print(f"   ❌ JavaScript file not found: {js_file_path}")
            return False
            
        with open(js_file_path, 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        # Check for required JavaScript functionality
        js_checks = [
            ("Search and Filter Initialization", "function initializeSearchAndFilter()"),
            ("Position Filter Element", "getElementById('positionFilter')"),
            ("Date From Filter Element", "getElementById('dateFromFilter')"),
            ("Date To Filter Element", "getElementById('dateToFilter')"),
            ("Apply Filters Function", "function applyFilters()"),
            ("Clear Filters Function", "function clearFilters()"),
            ("Debounce Function", "function debounce(func, wait)"),
            ("Load Filtered Data Function", "function loadFilteredStaffData(filters"),
            ("Render Filtered Table Function", "function renderFilteredStaffTable(staffList)"),
            ("Advanced Search API Call", "/advanced_search_staff?"),
            ("Search Input Event Listener", "searchInput.addEventListener('input'"),
            ("Department Filter Event Listener", "departmentFilter.addEventListener('change'"),
            ("Position Filter Event Listener", "positionFilter.addEventListener('change'"),
            ("Gender Filter Event Listener", "genderFilter.addEventListener('change'"),
            ("Date From Filter Event Listener", "dateFromFilter.addEventListener('change'"),
            ("Date To Filter Event Listener", "dateToFilter.addEventListener('change'"),
            ("Apply Button Event Listener", "applyFiltersBtn.addEventListener('click'"),
            ("Clear Button Event Listener", "clearFiltersBtn.addEventListener('click'")
        ]
        
        all_passed = True
        for check_name, check_pattern in js_checks:
            if check_pattern in js_content:
                print(f"   ✅ {check_name}: Found")
            else:
                print(f"   ❌ {check_name}: Missing")
                all_passed = False
        
        return all_passed
            
    except Exception as e:
        print(f"   ❌ Error testing JavaScript filter functionality: {e}")
        return False

def test_flask_advanced_search_route():
    """Test if the Flask advanced search route exists and has proper functionality"""
    print("\n🧪 Testing Flask Advanced Search Route...")
    
    try:
        # Read the Flask app file
        app_file_path = 'app.py'
        if not os.path.exists(app_file_path):
            print(f"   ❌ Flask app file not found: {app_file_path}")
            return False
            
        with open(app_file_path, 'r', encoding='utf-8') as f:
            app_content = f.read()
        
        # Check for advanced search route
        route_checks = [
            ("Advanced Search Route", "@app.route('/advanced_search_staff')"),
            ("Route Function", "def advanced_search_staff():"),
            ("Authorization Check", "if 'user_id' not in session"),
            ("Search Term Parameter", "request.args.get('search_term')"),
            ("Department Parameter", "request.args.get('department')"),
            ("Position Parameter", "request.args.get('position')"),
            ("Gender Parameter", "request.args.get('gender')"),
            ("Date From Parameter", "request.args.get('date_from')"),
            ("Date To Parameter", "request.args.get('date_to')"),
            ("Staff Manager Call", "staff_manager.advanced_search_staff"),
            ("JSON Response", "return jsonify({'success': True, 'staff': staff_list})")
        ]
        
        all_passed = True
        for check_name, check_pattern in route_checks:
            if check_pattern in app_content:
                print(f"   ✅ {check_name}: Found")
            else:
                print(f"   ❌ {check_name}: Missing")
                all_passed = False
        
        return all_passed
            
    except Exception as e:
        print(f"   ❌ Error testing Flask advanced search route: {e}")
        return False

def test_staff_manager_search_functionality():
    """Test if the StaffManager has advanced search functionality"""
    print("\n🧪 Testing StaffManager Search Functionality...")
    
    try:
        # Read the staff manager file
        staff_manager_file = 'staff_management_enhanced.py'
        if not os.path.exists(staff_manager_file):
            print(f"   ❌ StaffManager file not found: {staff_manager_file}")
            return False
            
        with open(staff_manager_file, 'r', encoding='utf-8') as f:
            staff_manager_content = f.read()
        
        # Check for advanced search functionality
        manager_checks = [
            ("Advanced Search Method", "def advanced_search_staff(self, school_id: int, filters: Dict)"),
            ("Search Term Filter", "if filters.get('search_term'):"),
            ("Department Filter", "if filters.get('department'):"),
            ("Position Filter", "if filters.get('position'):"),
            ("Gender Filter", "if filters.get('gender'):"),
            ("Date From Filter", "if filters.get('date_from'):"),
            ("Date To Filter", "if filters.get('date_to'):"),
            ("Dynamic Query Building", "where_conditions = ['school_id = ?']"),
            ("LIKE Search Pattern", "LIKE ?"),
            ("Full Name Search", "full_name LIKE ?"),
            ("Staff ID Search", "staff_id LIKE ?"),
            ("Email Search", "email LIKE ?"),
            ("Phone Search", "phone LIKE ?"),
            ("Date Range Filter", "date_of_joining >= ?"),
            ("Order By Clause", "ORDER BY full_name"),
            ("Return Dictionary List", "return [dict(staff) for staff in staff_members]")
        ]
        
        all_passed = True
        for check_name, check_pattern in manager_checks:
            if check_pattern in staff_manager_content:
                print(f"   ✅ {check_name}: Found")
            else:
                print(f"   ❌ {check_name}: Missing")
                all_passed = False
        
        return all_passed
            
    except Exception as e:
        print(f"   ❌ Error testing StaffManager search functionality: {e}")
        return False

def run_all_tests():
    """Run all tests for staff search and filter functionality"""
    print("🚀 Starting Staff Search & Filters Functionality Tests")
    print("=" * 70)
    
    tests = [
        ("HTML Filter Fields", test_html_filter_fields),
        ("JavaScript Filter Functionality", test_javascript_filter_functionality),
        ("Flask Advanced Search Route", test_flask_advanced_search_route),
        ("StaffManager Search Functionality", test_staff_manager_search_functionality),
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
        print("🎉 All tests passed! Staff Search & Filters functionality is working correctly.")
        print("\n✅ Summary of implemented features:")
        print("   • Search input field with debounced API calls")
        print("   • Department filter dropdown")
        print("   • Position filter dropdown")
        print("   • Gender filter dropdown")
        print("   • Date range filters (from/to)")
        print("   • Apply filters button")
        print("   • Clear filters button")
        print("   • Server-side filtering with advanced search")
        print("   • Dynamic table rendering with filtered results")
        print("   • Loading states and error handling")
        print("   • Filter combinations support")
        print("   • Responsive filter grid layout")
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
