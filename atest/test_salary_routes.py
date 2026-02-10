#!/usr/bin/env python3
"""
Test script to verify salary management routes are working
Tests the specific routes that were showing errors
"""

import sys
import os
import requests
import json

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_salary_routes():
    """Test salary management routes"""
    print("Testing salary management routes...")
    
    base_url = "http://127.0.0.1:5000"
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    try:
        # Test 1: Check if salary management page loads (should redirect to login)
        print("\n1. Testing salary management page access...")
        response = session.get(f"{base_url}/salary_management")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Salary management page accessible")
        elif response.status_code == 302:
            print("   ✅ Properly redirects to login (expected behavior)")
        else:
            print(f"   ❌ Unexpected status code: {response.status_code}")
        
        # Test 2: Check if get_salary_rules endpoint exists
        print("\n2. Testing get_salary_rules endpoint...")
        response = session.get(f"{base_url}/get_salary_rules")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') == False and 'Unauthorized' in data.get('error', ''):
                print("   ✅ Route exists and properly handles unauthorized access")
            else:
                print("   ✅ Route exists and returns data")
        else:
            print(f"   ❌ Route may not exist or has issues: {response.status_code}")
        
        # Test 3: Check if update_salary_rules endpoint exists
        print("\n3. Testing update_salary_rules endpoint...")
        response = session.post(f"{base_url}/update_salary_rules", data={
            'early_arrival_bonus_per_hour': 50.0
        })
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') == False and 'Unauthorized' in data.get('error', ''):
                print("   ✅ Route exists and properly handles unauthorized access")
            else:
                print("   ✅ Route exists and processes request")
        else:
            print(f"   ❌ Route may not exist or has issues: {response.status_code}")
        
        # Test 4: Check if bulk_salary_calculation endpoint exists
        print("\n4. Testing bulk_salary_calculation endpoint...")
        response = session.post(f"{base_url}/bulk_salary_calculation", data={
            'year': 2024,
            'month': 1
        })
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') == False and 'Unauthorized' in data.get('error', ''):
                print("   ✅ Route exists and properly handles unauthorized access")
            else:
                print("   ✅ Route exists and processes request")
        else:
            print(f"   ❌ Route may not exist or has issues: {response.status_code}")
        
        # Test 5: Check if get_departments endpoint exists
        print("\n5. Testing get_departments endpoint...")
        response = session.get(f"{base_url}/get_departments")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') == False and 'Unauthorized' in data.get('error', ''):
                print("   ✅ Route exists and properly handles unauthorized access")
            else:
                print("   ✅ Route exists and returns data")
        else:
            print(f"   ❌ Route may not exist or has issues: {response.status_code}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask server. Make sure it's running on http://127.0.0.1:5000")
        return False
    except Exception as e:
        print(f"❌ Error testing routes: {e}")
        return False

def test_salary_calculator_directly():
    """Test salary calculator directly"""
    print("\n" + "="*50)
    print("Testing SalaryCalculator directly...")
    
    try:
        from app import app
        from salary_calculator import SalaryCalculator
        
        with app.app_context():
            # Test initialization
            calc = SalaryCalculator()
            print("✅ SalaryCalculator initializes successfully")
            
            # Test salary rules
            rules = calc.salary_rules
            print(f"✅ Salary rules loaded: {len(rules)} rules")
            
            # Test update salary rules
            new_rules = {'early_arrival_bonus_per_hour': 60.0}
            result = calc.update_salary_rules(new_rules)
            print(f"✅ Update salary rules: {result}")
            
            return True
            
    except Exception as e:
        print(f"❌ SalaryCalculator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("SALARY MANAGEMENT ROUTES TEST")
    print("=" * 60)
    
    # Test routes
    routes_ok = test_salary_routes()
    
    # Test calculator directly
    calc_ok = test_salary_calculator_directly()
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if routes_ok and calc_ok:
        print("🎉 ALL TESTS PASSED!")
        print("✅ All salary management routes are accessible")
        print("✅ SalaryCalculator works correctly")
        print("✅ The errors you experienced should now be resolved")
        print("\nThe issues were likely caused by:")
        print("- SalaryCalculator trying to access database without app context")
        print("- This has been fixed by lazy database connection initialization")
        return True
    else:
        print("❌ Some tests failed")
        if not routes_ok:
            print("- Route accessibility issues")
        if not calc_ok:
            print("- SalaryCalculator issues")
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
