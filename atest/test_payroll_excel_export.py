#!/usr/bin/env python3

"""
Test Excel export functionality for the Enhanced Payroll Summary Report
"""

import datetime
import calendar
from app import app

def test_payroll_summary_excel_export():
    """Test the Excel export functionality specifically"""
    
    with app.app_context():
        from app import get_db
        db = get_db()
        
        # Get correct school_id
        staff_schools = db.execute("SELECT DISTINCT school_id FROM staff WHERE is_active = 1").fetchall()
        actual_school_id = staff_schools[0]['school_id'] if staff_schools else 1
        
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = 1
                sess['user_type'] = 'admin'
                sess['school_id'] = actual_school_id
        
            # Current month date range
            today = datetime.datetime.now()
            start_date = f"{today.year}-{str(today.month).zfill(2)}-01"
            last_day = min(today.day, calendar.monthrange(today.year, today.month)[1])
            end_date = f"{today.year}-{str(today.month).zfill(2)}-{str(last_day).zfill(2)}"
            
            print("=" * 60)
            print("TESTING PAYROLL SUMMARY EXCEL EXPORT")
            print("=" * 60)
            
            # Test Excel export
            params = {
                'report_type': 'payroll_summary',
                'from_date': start_date,
                'to_date': end_date,
                'format': 'excel'
            }
            
            response = client.get('/generate_admin_report', query_string=params)
            
            print(f"📊 Excel Export Test Results:")
            print(f"   Status Code: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('Content-Type')}")
            print(f"   Content-Length: {len(response.data)} bytes")
            
            content_disposition = response.headers.get('Content-Disposition', '')
            print(f"   Content-Disposition: {content_disposition}")
            
            if response.status_code == 200 and 'spreadsheet' in response.headers.get('Content-Type', ''):
                print("✅ Excel export successful!")
                
                # Test with department filter
                print(f"\n🧪 Testing Department Filter...")
                dept_params = {
                    'report_type': 'payroll_summary',
                    'from_date': start_date,
                    'to_date': end_date,
                    'department': 'Administration',
                    'format': 'excel'
                }
                
                dept_response = client.get('/generate_admin_report', query_string=dept_params)
                print(f"   Department Filter Status: {dept_response.status_code}")
                print(f"   Department Filter Size: {len(dept_response.data)} bytes")
                
                if dept_response.status_code == 200:
                    print("✅ Department filtering works with Excel export")
                
                return True
            else:
                print("❌ Excel export failed")
                print(f"   Response: {response.get_data(as_text=True)[:500]}")
                return False

if __name__ == "__main__":
    success = test_payroll_summary_excel_export()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: Excel Export Test")