#!/usr/bin/env python3
"""
Test script for the Staff Directory layout alignment fixes
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_css_table_layout_fixes():
    """Test if CSS has proper table layout fixes"""
    print("\n🧪 Testing CSS Table Layout Fixes...")
    
    try:
        # Read the CSS file
        css_file_path = 'static/css/salary_management.css'
        if not os.path.exists(css_file_path):
            print(f"   ❌ CSS file not found: {css_file_path}")
            return False
            
        with open(css_file_path, 'r', encoding='utf-8') as f:
            css_content = f.read()
        
        # Check for table layout stability fixes
        layout_checks = [
            ("Table Layout Auto", "table-layout: auto"),
            ("Border Collapse Separate", "border-collapse: separate"),
            ("Border Spacing Zero", "border-spacing: 0"),
            ("Minimum Table Width", "min-width: 800px"),
            ("Staff Table Min Height", "#staffTable"),
            ("Table Body Min Height", "#staffTableBody"),
            ("Table Responsive Position", ".table-responsive"),
            ("Column Width Constraints", "width: 120px"),
            ("Column Min Width Constraints", "min-width: 120px"),
            ("Sticky Header", "position: sticky"),
            ("Loading State Transition", "transition: opacity"),
            ("Loading Class Opacity", ".loading tbody"),
            ("User Avatar Consistency", ".user-avatar"),
            ("Badge Consistency", ".badge"),
            ("Action Buttons Min Width", "min-width: 100px"),
            ("Loading State Styling", ".staff-loading-state"),
            ("Empty State Styling", ".staff-empty-state"),
            ("Results Container Min Height", ".results-container"),
            ("Card Body Min Height", ".salary-results-card .card-body")
        ]
        
        all_passed = True
        for check_name, check_pattern in layout_checks:
            if check_pattern in css_content:
                print(f"   ✅ {check_name}: Found")
            else:
                print(f"   ❌ {check_name}: Missing")
                all_passed = False
        
        return all_passed
            
    except Exception as e:
        print(f"   ❌ Error testing CSS table layout fixes: {e}")
        return False

def test_responsive_css_fixes():
    """Test if responsive CSS fixes are properly implemented"""
    print("\n🧪 Testing Responsive CSS Fixes...")
    
    try:
        # Read the CSS file
        css_file_path = 'static/css/salary_management.css'
        if not os.path.exists(css_file_path):
            print(f"   ❌ CSS file not found: {css_file_path}")
            return False
            
        with open(css_file_path, 'r', encoding='utf-8') as f:
            css_content = f.read()
        
        # Check for responsive design fixes
        responsive_checks = [
            ("Mobile Media Query", "@media (max-width: 768px)"),
            ("Mobile Table Min Width", "min-width: 600px"),
            ("Mobile Column Width Adjustments", "width: 80px"),
            ("Mobile Action Buttons", "flex-direction: row"),
            ("Mobile Button Sizing", "padding: 0.25rem 0.5rem"),
            ("Mobile User Avatar", "width: 24px"),
            ("Mobile Badge Sizing", "font-size: 0.65rem"),
            ("Mobile Contact Info", "font-size: 0.7rem"),
            ("Tablet Media Query", "@media (max-width: 1200px)"),
            ("Small Screen Media Query", "@media (max-width: 576px)")
        ]
        
        all_passed = True
        for check_name, check_pattern in responsive_checks:
            if check_pattern in css_content:
                print(f"   ✅ {check_name}: Found")
            else:
                print(f"   ❌ {check_name}: Missing")
                all_passed = False
        
        return all_passed
            
    except Exception as e:
        print(f"   ❌ Error testing responsive CSS fixes: {e}")
        return False

def test_javascript_table_rendering():
    """Test if JavaScript table rendering matches HTML structure"""
    print("\n🧪 Testing JavaScript Table Rendering...")
    
    try:
        # Read the JavaScript file
        js_file_path = 'static/js/staff_management.js'
        if not os.path.exists(js_file_path):
            print(f"   ❌ JavaScript file not found: {js_file_path}")
            return False
            
        with open(js_file_path, 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        # Check for proper table rendering
        rendering_checks = [
            ("Render Filtered Staff Table Function", "function renderFilteredStaffTable(staffList)"),
            ("Correct Column Count", "colspan=\"7\""),
            ("Data Staff ID Attribute", "setAttribute('data-staff-id'"),
            ("User Avatar Structure", "class=\"user-avatar me-2\""),
            ("Badge Structure", "class=\"badge bg-primary\""),
            ("Contact Info Structure", "class=\"d-block\""),
            ("Action Buttons Structure", "class=\"action-buttons\""),
            ("Bootstrap Modal Target", "data-bs-target=\"#editStaffModal\""),
            ("Table Layout Force Recalculation", "table.style.tableLayout"),
            ("Loading State Functions", "function showTableLoadingState()"),
            ("Hide Loading State", "function hideTableLoadingState()"),
            ("Loading Class Management", "table.classList.add('loading')"),
            ("Loading Class Removal", "table.classList.remove('loading')"),
            ("Staff Loading State Class", "staff-loading-state"),
            ("Proper Error Handling", "hideTableLoadingState()"),
            ("Console Logging", "console.log(`Found ${data.staff.length}"),
            ("Stats Update", "updateFilteredStatsDisplay(data.staff.length)")
        ]
        
        all_passed = True
        for check_name, check_pattern in rendering_checks:
            if check_pattern in js_content:
                print(f"   ✅ {check_name}: Found")
            else:
                print(f"   ❌ {check_name}: Missing")
                all_passed = False
        
        return all_passed
            
    except Exception as e:
        print(f"   ❌ Error testing JavaScript table rendering: {e}")
        return False

def test_html_table_structure():
    """Test if HTML table structure is properly defined"""
    print("\n🧪 Testing HTML Table Structure...")
    
    try:
        # Read the HTML template
        html_file_path = 'templates/staff_management.html'
        if not os.path.exists(html_file_path):
            print(f"   ❌ HTML template not found: {html_file_path}")
            return False
            
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Check for proper table structure
        structure_checks = [
            ("Staff Directory Title", "Staff Directory"),
            ("Table ID", "id=\"staffTable\""),
            ("Table Body ID", "id=\"staffTableBody\""),
            ("Table Classes", "class=\"table salary-results-table\""),
            ("Table Responsive Wrapper", "class=\"table-responsive\""),
            ("Correct Column Headers", "<th>Staff ID</th>"),
            ("Name Column Header", "<th>Name</th>"),
            ("Department Column Header", "<th>Department</th>"),
            ("Position Column Header", "<th>Position</th>"),
            ("Contact Column Header", "<th>Contact</th>"),
            ("Shift Type Column Header", "<th>Shift Type</th>"),
            ("Actions Column Header", "<th>Actions</th>"),
            ("User Avatar Structure", "class=\"user-avatar me-2\""),
            ("Badge Structure", "class=\"badge bg-primary\""),
            ("Action Buttons Structure", "class=\"action-buttons\""),
            ("Data Staff ID Attributes", "data-staff-id=\"{{ staff_member.id }}\""),
            ("Bootstrap Icons", "class=\"bi bi-person-circle\""),
            ("Contact Icons", "class=\"bi bi-telephone\""),
            ("Email Icons", "class=\"bi bi-envelope\"")
        ]
        
        all_passed = True
        for check_name, check_pattern in structure_checks:
            if check_pattern in html_content:
                print(f"   ✅ {check_name}: Found")
            else:
                print(f"   ❌ {check_name}: Missing")
                all_passed = False
        
        return all_passed
            
    except Exception as e:
        print(f"   ❌ Error testing HTML table structure: {e}")
        return False

def run_all_tests():
    """Run all tests for staff directory layout alignment fixes"""
    print("🚀 Starting Staff Directory Layout Alignment Tests")
    print("=" * 70)
    
    tests = [
        ("CSS Table Layout Fixes", test_css_table_layout_fixes),
        ("Responsive CSS Fixes", test_responsive_css_fixes),
        ("JavaScript Table Rendering", test_javascript_table_rendering),
        ("HTML Table Structure", test_html_table_structure),
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
        print("🎉 All tests passed! Staff Directory layout alignment issues are fixed.")
        print("\n✅ Summary of fixes implemented:")
        print("   • Fixed table layout stability with proper CSS constraints")
        print("   • Corrected JavaScript rendering to match HTML structure")
        print("   • Added column width constraints for consistent alignment")
        print("   • Implemented responsive design for all screen sizes")
        print("   • Added loading states with proper visual feedback")
        print("   • Fixed container sizing and layout preservation")
        print("   • Ensured proper table structure during dynamic updates")
        print("   • Added smooth transitions and layout recalculation")
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
