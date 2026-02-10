#!/usr/bin/env python3
"""
Debug script to identify the exact cause of salary management errors
This will test the routes directly and show detailed error information
"""

import sys
import os
import requests
import json

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_with_session():
    """Test salary routes with a proper session"""
    print("🔍 DEBUGGING SALARY MANAGEMENT ERRORS")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:5000"
    session = requests.Session()
    
    try:
        # Step 1: Try to login with test admin
        print("\n1. Testing login with test admin...")
        login_data = {
            'school_id': '1',  # Add school_id
            'username': 'testadmin',
            'password': 'testpass123'
        }

        login_response = session.post(f"{base_url}/login", data=login_data)
        print(f"   Login Status Code: {login_response.status_code}")
        
        if login_response.status_code == 200:
            print("   ✅ Login successful")
        elif login_response.status_code == 302:
            print("   ✅ Login redirect (likely successful)")
        else:
            print(f"   ❌ Login failed: {login_response.status_code}")
            print(f"   Response: {login_response.text[:200]}...")
            return False
        
        # Step 2: Test salary management page access
        print("\n2. Testing salary management page access...")
        salary_page = session.get(f"{base_url}/salary_management")
        print(f"   Status Code: {salary_page.status_code}")
        
        if salary_page.status_code == 200:
            print("   ✅ Salary management page accessible")
        else:
            print(f"   ❌ Cannot access salary management page")
            print(f"   Response: {salary_page.text[:200]}...")
        
        # Step 3: Test get_salary_rules
        print("\n3. Testing get_salary_rules endpoint...")
        rules_response = session.get(f"{base_url}/get_salary_rules")
        print(f"   Status Code: {rules_response.status_code}")
        
        if rules_response.status_code == 200:
            try:
                rules_data = rules_response.json()
                print(f"   Response: {rules_data}")
                if rules_data.get('success'):
                    print("   ✅ Get salary rules working")
                else:
                    print(f"   ❌ Get salary rules error: {rules_data.get('error')}")
            except:
                print(f"   ❌ Invalid JSON response: {rules_response.text[:200]}...")
        else:
            print(f"   ❌ Get salary rules failed: {rules_response.status_code}")
        
        # Step 4: Test update_salary_rules
        print("\n4. Testing update_salary_rules endpoint...")
        update_data = {
            'early_arrival_bonus_per_hour': '50.0',
            'early_departure_penalty_per_hour': '100.0',
            'late_arrival_penalty_per_hour': '75.0',
            'overtime_rate_multiplier': '1.5',
            'absent_day_deduction_rate': '1.0',
            'on_duty_rate': '1.0'
        }
        
        update_response = session.post(f"{base_url}/update_salary_rules", data=update_data)
        print(f"   Status Code: {update_response.status_code}")
        
        if update_response.status_code == 200:
            try:
                update_result = update_response.json()
                print(f"   Response: {update_result}")
                if update_result.get('success'):
                    print("   ✅ Update salary rules working")
                else:
                    print(f"   ❌ Update salary rules error: {update_result.get('error')}")
            except:
                print(f"   ❌ Invalid JSON response: {update_response.text[:200]}...")
        else:
            print(f"   ❌ Update salary rules failed: {update_response.status_code}")
            print(f"   Response: {update_response.text[:200]}...")
        
        # Step 5: Test bulk_salary_calculation
        print("\n5. Testing bulk_salary_calculation endpoint...")
        calc_data = {
            'year': '2024',
            'month': '1'
        }
        
        calc_response = session.post(f"{base_url}/bulk_salary_calculation", data=calc_data)
        print(f"   Status Code: {calc_response.status_code}")
        
        if calc_response.status_code == 200:
            try:
                calc_result = calc_response.json()
                print(f"   Response: {calc_result}")
                if calc_result.get('success'):
                    print("   ✅ Bulk salary calculation working")
                    print(f"   Total staff processed: {calc_result.get('total_staff', 0)}")
                else:
                    print(f"   ❌ Bulk salary calculation error: {calc_result.get('error')}")
            except:
                print(f"   ❌ Invalid JSON response: {calc_response.text[:200]}...")
        else:
            print(f"   ❌ Bulk salary calculation failed: {calc_response.status_code}")
            print(f"   Response: {calc_response.text[:200]}...")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask server. Make sure it's running on http://127.0.0.1:5000")
        return False
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_direct_import():
    """Test importing and using salary calculator directly"""
    print("\n" + "=" * 60)
    print("🔍 TESTING DIRECT SALARY CALCULATOR IMPORT")
    print("=" * 60)
    
    try:
        print("\n1. Testing Flask app import...")
        from app import app
        print("   ✅ Flask app imported successfully")
        
        print("\n2. Testing SalaryCalculator import...")
        from salary_calculator import SalaryCalculator
        print("   ✅ SalaryCalculator imported successfully")
        
        print("\n3. Testing SalaryCalculator initialization...")
        with app.app_context():
            calc = SalaryCalculator()
            print("   ✅ SalaryCalculator initialized successfully")
            
            print("\n4. Testing salary rules access...")
            rules = calc.salary_rules
            print(f"   ✅ Salary rules loaded: {len(rules)} rules")
            
            print("\n5. Testing salary rules update...")
            new_rules = {'early_arrival_bonus_per_hour': 60.0}
            result = calc.update_salary_rules(new_rules)
            print(f"   Result: {result}")
            
            if result.get('success'):
                print("   ✅ Salary rules update working directly")
            else:
                print(f"   ❌ Salary rules update failed: {result.get('error')}")
            
            return True
            
    except Exception as e:
        print(f"❌ Direct import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all debugging tests"""
    print("🚨 SALARY MANAGEMENT ERROR DEBUGGING")
    print("This will help identify the exact cause of your errors")
    print("=" * 60)
    
    # Test direct import first
    direct_ok = test_direct_import()
    
    # Test with HTTP requests
    http_ok = test_with_session()
    
    print("\n" + "=" * 60)
    print("🔍 DEBUGGING SUMMARY")
    print("=" * 60)
    
    if direct_ok and http_ok:
        print("🎉 All tests passed - the issue might be with browser/session")
        print("\n💡 POSSIBLE SOLUTIONS:")
        print("1. Clear your browser cache and cookies")
        print("2. Try logging out and logging back in")
        print("3. Try using an incognito/private browser window")
        print("4. Check if you're logged in as the correct user type (admin/company_admin)")
    elif direct_ok and not http_ok:
        print("❌ HTTP requests failing but direct import works")
        print("\n💡 POSSIBLE CAUSES:")
        print("1. Session/authentication issues")
        print("2. CSRF token problems")
        print("3. Form data format issues")
    elif not direct_ok:
        print("❌ Direct import failing - core system issue")
        print("\n💡 POSSIBLE CAUSES:")
        print("1. Database connection issues")
        print("2. Missing dependencies")
        print("3. Code syntax errors")
    else:
        print("❌ Mixed results - need further investigation")
    
    return direct_ok and http_ok

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
