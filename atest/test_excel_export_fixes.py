#!/usr/bin/env python3
"""
Test the fixed Excel export functionality
"""

import requests
import sys
import os
import time

def test_flask_app_excel_exports():
    """Test Excel export routes when Flask app is running"""
    
    base_url = "http://localhost:5000"  # Assuming Flask runs on default port
    
    print("Testing Excel Export Functionality")
    print("=" * 50)
    
    # Test if Flask app is running
    try:
        response = requests.get(base_url, timeout=5)
        print(f"✓ Flask app is running (Status: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"✗ Flask app is not running: {e}")
        print("Please start the Flask app with: python app.py")
        return False
    
    # Test staff Excel export endpoint
    print("\nTesting Staff Excel Export...")
    try:
        # This would normally require authentication, but we'll test the endpoint existence
        response = requests.get(f"{base_url}/export_staff_excel", allow_redirects=False)
        if response.status_code in [200, 302, 401, 403]:  # 302 redirect to login is expected
            print(f"✓ Staff Excel export endpoint exists (Status: {response.status_code})")
        else:
            print(f"✗ Unexpected response: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"✗ Staff Excel export test failed: {e}")
    
    # Test dashboard export endpoint
    print("\nTesting Dashboard Export...")
    try:
        response = requests.get(f"{base_url}/admin/export_dashboard_data", allow_redirects=False)
        if response.status_code in [200, 302, 401, 403]:
            print(f"✓ Dashboard export endpoint exists (Status: {response.status_code})")
        else:
            print(f"✗ Unexpected response: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"✗ Dashboard export test failed: {e}")
    
    # Test report export endpoint
    print("\nTesting Report Export...")
    try:
        response = requests.get(f"{base_url}/export_report_excel", allow_redirects=False)
        if response.status_code in [200, 302, 401, 403]:
            print(f"✓ Report export endpoint exists (Status: {response.status_code})")
        else:
            print(f"✗ Unexpected response: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"✗ Report export test failed: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed. If endpoints exist, the Excel export functionality should work.")
    print("Note: Authentication required for actual file downloads.")
    
    return True

def generate_test_instructions():
    """Generate step-by-step testing instructions"""
    
    instructions = """
EXCEL EXPORT FUNCTIONALITY - TESTING GUIDE
==========================================

FIXES IMPLEMENTED:
1. ✓ Fixed /export_staff_excel route to generate proper .xlsx files instead of CSV
2. ✓ Added proper Excel content-type headers (application/vnd.openxmlformats-officedocument.spreadsheetml.sheet)
3. ✓ Implemented comprehensive admin dashboard export functionality
4. ✓ Added multiple export options with proper modal dialogs
5. ✓ Enhanced JavaScript export handlers with loading states
6. ✓ Added export for applications (leave, on-duty, permission)
7. ✓ Proper error handling and user feedback

MANUAL TESTING STEPS:

1. START THE FLASK APPLICATION:
   - Open terminal in: d:\\VISHNRX\\staffongoingmohannew-updation
   - Run: python app.py
   - Verify app starts without errors

2. LOGIN AS ADMIN:
   - Go to: http://localhost:5000
   - Login with admin credentials
   - Navigate to Admin Dashboard

3. TEST STAFF EXCEL EXPORT:
   - Click "Export Data" button in Quick Actions section
   - Select "Export to Excel" option
   - Verify .xlsx file downloads properly
   - Open file in Excel/LibreOffice to verify formatting

4. TEST DASHBOARD EXPORT:
   - Click "Export" button in header actions
   - Try each export option:
     * Complete Dashboard
     * Today's Attendance  
     * Staff Profiles
     * Applications
   - Verify all generate proper .xlsx files

5. TEST STAFF WITH ATTENDANCE EXPORT:
   - Click "Export Data" → "Staff with Attendance"
   - Select date range
   - Verify comprehensive report downloads

6. VERIFY EXCEL FILES:
   - Files should have .xlsx extension
   - Should open in Excel/LibreOffice without errors
   - Should contain proper headers and formatting
   - Should include all expected data fields

EXPECTED BEHAVIORS:
- Export buttons show loading spinners during processing
- Files download automatically with timestamp in filename
- Excel files contain multiple sheets where applicable
- Proper error messages shown if export fails
- Modals close automatically after successful export

TROUBLESHOOTING:
- If export fails: Check browser console for JavaScript errors
- If server errors: Check Flask terminal output
- If file corruption: Verify openpyxl library installation
- If authentication issues: Ensure proper admin login

BROWSER COMPATIBILITY:
- Chrome/Edge: Full support
- Firefox: Full support  
- Safari: Should work with modern versions
- IE: Not supported (use modern browser)

FILE LOCATIONS:
- Downloads folder: Check for exported .xlsx files
- Naming pattern: [type]_[timestamp].xlsx
- Example: staff_details_20240910_143022.xlsx

SUCCESS CRITERIA:
✓ Export buttons trigger proper download flows
✓ Generated files are valid Excel format (.xlsx)
✓ Files contain expected data with proper formatting
✓ No JavaScript errors in browser console
✓ No server errors in Flask terminal
✓ Files open correctly in Excel applications
"""
    
    print(instructions)
    
    # Save instructions to file
    with open('EXCEL_EXPORT_TESTING_GUIDE.txt', 'w', encoding='utf-8') as f:
        f.write(instructions)
    
    print(f"\nTesting guide saved to: EXCEL_EXPORT_TESTING_GUIDE.txt")

def main():
    """Main test function"""
    print("Excel Export Functionality - Post-Fix Testing")
    print("=" * 60)
    
    # Generate testing instructions
    generate_test_instructions()
    
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("1. Start the Flask application: python app.py")
    print("2. Follow the testing guide above")
    print("3. Report any issues found during testing")
    
    # Test if Flask app is running (optional)
    user_input = input("\nTest live Flask app endpoints? (y/n): ").strip().lower()
    if user_input == 'y':
        test_flask_app_excel_exports()

if __name__ == "__main__":
    main()
