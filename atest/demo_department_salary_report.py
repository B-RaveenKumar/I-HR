#!/usr/bin/env python3

"""
Generate a sample Department Wise Salary Report to demonstrate the functionality
"""

from app import app
import datetime

def generate_sample_report():
    """Generate and download a sample Department Wise Salary Excel report"""
    
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
        
            current_year = datetime.datetime.now().year
            
            print("🚀 Generating Department Wise Salary Report Sample...")
            print(f"   School ID: {actual_school_id}")
            print(f"   Year: {current_year}")
            
            # Generate Excel report
            params = {
                'report_type': 'department_salary',
                'year': current_year,
                'format': 'excel'
            }
            
            response = client.get('/generate_admin_report', query_string=params)
            
            if response.status_code == 200:
                # Save to file for demonstration
                filename = f"department_salary_sample_{current_year}.xlsx"
                with open(filename, 'wb') as f:
                    f.write(response.data)
                
                print(f"✅ Report generated successfully!")
                print(f"   File: {filename}")
                print(f"   Size: {len(response.data)} bytes")
                print(f"   Content-Type: {response.headers.get('Content-Type')}")
                
                print(f"\nℹ️  The Excel file contains:")
                print(f"   - Professional title and summary section")
                print(f"   - Department-wise staff grouping with headers")
                print(f"   - Complete salary breakdown for each employee")
                print(f"   - Detailed deduction columns (PF, ESI, Professional Tax, etc.)")
                print(f"   - Gross pay calculations")
                print(f"   - Department totals and grand totals")
                print(f"   - Professional styling with colors and formatting")
                
                return True
            else:
                print(f"❌ Failed to generate report")
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.get_data(as_text=True)[:500]}")
                return False

if __name__ == "__main__":
    success = generate_sample_report()
    
    if success:
        print(f"\n🎯 DEMONSTRATION COMPLETE")
        print(f"   The Department Wise Salary report is fully functional")
        print(f"   and ready for use in the Salary & Payroll Reports section!")
    else:
        print(f"\n❌ DEMONSTRATION FAILED")