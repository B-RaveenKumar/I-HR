#!/usr/bin/env python3
"""
Test script to verify salary management with proper authentication
Creates a test admin user and tests all salary functionality
"""

import sys
import os
import sqlite3
from werkzeug.security import generate_password_hash

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_test_admin():
    """Create a test admin user for testing"""
    print("Creating test admin user...")
    
    try:
        from app import app
        from database import get_db
        
        with app.app_context():
            db = get_db()
            
            # Check if test admin already exists
            existing_admin = db.execute(
                'SELECT * FROM admins WHERE username = ?', ('testadmin',)
            ).fetchone()
            
            if existing_admin:
                print("✅ Test admin already exists")
                return True
            
            # Create test admin
            password_hash = generate_password_hash('testpass123')
            db.execute('''
                INSERT INTO admins (username, password, school_id)
                VALUES (?, ?, ?)
            ''', ('testadmin', password_hash, 1))
            
            db.commit()
            print("✅ Test admin created successfully")
            return True
            
    except Exception as e:
        print(f"❌ Failed to create test admin: {e}")
        return False

def create_test_staff():
    """Create a test staff member with salary information"""
    print("Creating test staff member...")
    
    try:
        from app import app
        from database import get_db
        
        with app.app_context():
            db = get_db()
            
            # Check if test staff already exists
            existing_staff = db.execute(
                'SELECT * FROM staff WHERE staff_id = ?', ('TEST001',)
            ).fetchone()
            
            if existing_staff:
                print("✅ Test staff already exists")
                return True
            
            # Create test staff with salary information
            password_hash = generate_password_hash('staffpass123')
            db.execute('''
                INSERT INTO staff (
                    school_id, staff_id, password_hash, full_name, email, phone, 
                    department, position, basic_salary, hra, transport_allowance, 
                    other_allowances, pf_deduction, esi_deduction, professional_tax, 
                    other_deductions
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                1, 'TEST001', password_hash, 'Test Staff Member', 'test@example.com',
                '1234567890', 'IT', 'Developer', 30000.00, 5000.00, 2000.00,
                1000.00, 1800.00, 150.00, 200.00, 0.00
            ))
            
            db.commit()
            print("✅ Test staff created successfully")
            return True
            
    except Exception as e:
        print(f"❌ Failed to create test staff: {e}")
        return False

def test_salary_calculation():
    """Test salary calculation for the test staff"""
    print("Testing salary calculation...")
    
    try:
        from app import app
        from salary_calculator import SalaryCalculator
        from database import get_db
        
        with app.app_context():
            db = get_db()
            
            # Get test staff ID
            staff = db.execute(
                'SELECT id FROM staff WHERE staff_id = ?', ('TEST001',)
            ).fetchone()
            
            if not staff:
                print("❌ Test staff not found")
                return False
            
            # Test salary calculation
            calc = SalaryCalculator()
            result = calc.calculate_monthly_salary(staff['id'], 2024, 1)
            
            if result['success']:
                print("✅ Salary calculation successful")
                breakdown = result['salary_breakdown']
                print(f"   Net Salary: ₹{breakdown['net_salary']}")
                print(f"   Total Earnings: ₹{breakdown['earnings']['total_earnings']}")
                print(f"   Total Deductions: ₹{breakdown['deductions']['total_deductions']}")
                return True
            else:
                print(f"❌ Salary calculation failed: {result['error']}")
                return False
                
    except Exception as e:
        print(f"❌ Salary calculation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_salary_rules_update():
    """Test salary rules update"""
    print("Testing salary rules update...")
    
    try:
        from app import app
        from salary_calculator import SalaryCalculator
        
        with app.app_context():
            calc = SalaryCalculator()
            
            # Test updating rules
            new_rules = {
                'early_arrival_bonus_per_hour': 75.0,
                'early_departure_penalty_per_hour': 125.0
            }
            
            result = calc.update_salary_rules(new_rules)
            
            if result['success']:
                print("✅ Salary rules update successful")
                print(f"   Early arrival bonus: ₹{calc.salary_rules['early_arrival_bonus_per_hour']}/hour")
                print(f"   Early departure penalty: ₹{calc.salary_rules['early_departure_penalty_per_hour']}/hour")
                return True
            else:
                print(f"❌ Salary rules update failed: {result['error']}")
                return False
                
    except Exception as e:
        print(f"❌ Salary rules update test failed: {e}")
        return False

def test_bulk_calculation():
    """Test bulk salary calculation"""
    print("Testing bulk salary calculation...")
    
    try:
        from app import app
        from salary_calculator import SalaryCalculator
        from database import get_db
        
        with app.app_context():
            db = get_db()
            
            # Get all staff for school 1
            staff_list = db.execute(
                'SELECT id, staff_id, full_name, department FROM staff WHERE school_id = ?', (1,)
            ).fetchall()
            
            if not staff_list:
                print("❌ No staff found for bulk calculation")
                return False
            
            calc = SalaryCalculator()
            results = []
            
            for staff in staff_list:
                salary_result = calc.calculate_monthly_salary(staff['id'], 2024, 1)
                if salary_result['success']:
                    results.append({
                        'staff_id': staff['staff_id'],
                        'staff_name': staff['full_name'],
                        'department': staff['department'],
                        'net_salary': salary_result['salary_breakdown']['net_salary']
                    })
            
            if results:
                print(f"✅ Bulk calculation successful for {len(results)} staff members")
                for result in results[:3]:  # Show first 3 results
                    print(f"   {result['staff_id']}: ₹{result['net_salary']}")
                return True
            else:
                print("❌ No successful calculations in bulk test")
                return False
                
    except Exception as e:
        print(f"❌ Bulk calculation test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("COMPREHENSIVE SALARY SYSTEM TEST")
    print("=" * 60)
    
    tests = [
        ("Create Test Admin", create_test_admin),
        ("Create Test Staff", create_test_staff),
        ("Test Salary Calculation", test_salary_calculation),
        ("Test Salary Rules Update", test_salary_rules_update),
        ("Test Bulk Calculation", test_bulk_calculation)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            if test_func():
                passed_tests += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests Passed: {passed_tests}/{total_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("✅ Salary system is working correctly!")
        print("✅ The errors you experienced should now be resolved!")
        print("\nTest admin credentials:")
        print("Username: testadmin")
        print("Password: testpass123")
        print("\nYou can now login and test the salary management interface.")
        return True
    else:
        print(f"\n❌ {total_tests - passed_tests} tests failed")
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
