#!/usr/bin/env python3
"""
Simple test to verify the generate_admin_report endpoint works after the database column fix.
"""

import requests
import json
import sys
import os

def test_admin_report_endpoint():
    """Test the /generate_admin_report endpoint."""
    
    print("Testing /generate_admin_report endpoint...")
    print("=" * 50)
    
    # Test URL (assuming Flask app runs on localhost:5000)
    url = "http://localhost:5000/generate_admin_report"
    
    # Test data
    test_data = {
        "report_type": "staff",
        "parameters": {
            "start_date": "2025-01-01",
            "end_date": "2025-09-10",
            "department": ""
        }
    }
    
    try:
        # Make the request
        response = requests.post(url, json=test_data, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Content Type: {response.headers.get('content-type', 'Unknown')}")
        
        if response.status_code == 200:
            # Check if it's a file download
            content_disposition = response.headers.get('content-disposition', '')
            if 'attachment' in content_disposition:
                print("✅ File download response received!")
                print(f"Content-Disposition: {content_disposition}")
                print(f"File size: {len(response.content)} bytes")
                
                # Save file for verification
                filename = "test_staff_report.xlsx"
                with open(filename, 'wb') as f:
                    f.write(response.content)
                print(f"✅ File saved as: {filename}")
                
                return True
            else:
                # JSON response
                try:
                    result = response.json()
                    print(f"JSON Response: {json.dumps(result, indent=2)}")
                    return result.get('success', False)
                except:
                    print(f"Text Response: {response.text[:200]}...")
                    return False
        else:
            print(f"❌ Error response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - Flask app may not be running")
        print("💡 To test manually:")
        print("   1. Start the Flask app: python app.py")
        print("   2. Login as admin")
        print("   3. Try generating a report from the Reports & Analytics section")
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("Admin Report Endpoint Test")
    print("=" * 50)
    
    success = test_admin_report_endpoint()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ ENDPOINT TEST PASSED!")
    else:
        print("❌ ENDPOINT TEST FAILED OR APP NOT RUNNING")
    
    print("\nColumn Fix Summary:")
    print("- Fixed query to use actual database columns")
    print("- Replaced 's.allowances' with calculated total: (hra + transport_allowance + other_allowances)")
    print("- Replaced 's.deductions' with calculated total: (pf_deduction + esi_deduction + professional_tax + other_deductions)")
    print("- Net salary now correctly calculated from actual column values")
    
    print("\nTo verify the fix manually:")
    print("1. Start Flask app: python app.py")
    print("2. Login to admin dashboard")
    print("3. Go to Reports & Analytics section")
    print("4. Click 'Generate' on any report type")
    print("5. Verify Excel file downloads successfully")
