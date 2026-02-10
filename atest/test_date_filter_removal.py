#!/usr/bin/env python3
"""
Test script to verify the removal of date filter fields from staff management.
"""

import os
import sys

def test_html_changes():
    """Test that date filter fields are removed from HTML template"""
    print("🔍 Testing HTML template changes...")
    
    html_file = "templates/staff_management.html"
    if not os.path.exists(html_file):
        print(f"❌ Template file not found: {html_file}")
        return False
    
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that date filter fields are removed
    removed_elements = [
        'dateFromFilter',
        'dateToFilter',
        'Joined From',
        'Joined To',
        'calendar-date',
        'calendar-check'
    ]
    
    found_elements = []
    for element in removed_elements:
        if element in content:
            found_elements.append(element)
    
    if found_elements:
        print(f"❌ Still found date filter elements: {found_elements}")
        return False
    else:
        print("✅ Date filter fields successfully removed from HTML")
        return True

def test_javascript_changes():
    """Test that date filter logic is removed from JavaScript"""
    print("🔍 Testing JavaScript changes...")
    
    js_file = "static/js/staff_management.js"
    if not os.path.exists(js_file):
        print(f"❌ JavaScript file not found: {js_file}")
        return False
    
    with open(js_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that date filter variables and logic are removed
    removed_elements = [
        'dateFromFilter',
        'dateToFilter',
        'date_from:',
        'date_to:'
    ]
    
    found_elements = []
    for element in removed_elements:
        if element in content:
            found_elements.append(element)
    
    if found_elements:
        print(f"❌ Still found date filter logic: {found_elements}")
        return False
    else:
        print("✅ Date filter logic successfully removed from JavaScript")
        return True

def test_backend_changes():
    """Test that date filter handling is removed from backend"""
    print("🔍 Testing backend changes...")
    
    # Test app.py
    app_file = "app.py"
    if os.path.exists(app_file):
        with open(app_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for date filter parameters in staff search
        if "'date_from': request.args.get('date_from')" in content:
            print("❌ Still found date_from filter in app.py")
            return False
        
        if "'date_to': request.args.get('date_to')" in content:
            print("❌ Still found date_to filter in app.py")
            return False
    
    # Test staff_management_enhanced.py
    staff_file = "staff_management_enhanced.py"
    if os.path.exists(staff_file):
        with open(staff_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for date filter logic in advanced search
        if "filters.get('date_from')" in content:
            print("❌ Still found date_from logic in staff_management_enhanced.py")
            return False
        
        if "filters.get('date_to')" in content:
            print("❌ Still found date_to logic in staff_management_enhanced.py")
            return False
    
    print("✅ Date filter handling successfully removed from backend")
    return True

def test_remaining_filters():
    """Test that remaining filters are still present and functional"""
    print("🔍 Testing remaining filter functionality...")
    
    js_file = "static/js/staff_management.js"
    if not os.path.exists(js_file):
        print(f"❌ JavaScript file not found: {js_file}")
        return False
    
    with open(js_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that remaining filters are still present
    required_filters = [
        'searchInput',
        'departmentFilter',
        'positionFilter',
        'genderFilter'
    ]
    
    missing_filters = []
    for filter_name in required_filters:
        if filter_name not in content:
            missing_filters.append(filter_name)
    
    if missing_filters:
        print(f"❌ Missing required filters: {missing_filters}")
        return False
    else:
        print("✅ All remaining filters are present")
        return True

def main():
    """Run all tests"""
    print("🧪 Testing Date Filter Removal from Staff Management")
    print("=" * 60)
    
    tests = [
        ("HTML Template Changes", test_html_changes),
        ("JavaScript Changes", test_javascript_changes),
        ("Backend Changes", test_backend_changes),
        ("Remaining Filters", test_remaining_filters)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:<10} {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal Tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed! Date filters have been successfully removed.")
        print("\n📝 Changes Summary:")
        print("   • Removed 'Joined From' and 'Joined To' date input fields from HTML")
        print("   • Removed date filter variables and logic from JavaScript")
        print("   • Removed date filter handling from backend (app.py and staff_management_enhanced.py)")
        print("   • Preserved all other filter functionality (search, department, position, gender)")
        print("\n✨ The staff management filter section should now have a cleaner layout")
        print("   with only the essential search and filter controls.")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the changes.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
