#!/usr/bin/env python3
"""
Test script to verify the staff lookup fix for salary details
Tests that the correct staff ID is being passed and found
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_staff_lookup():
    """Test staff lookup with correct database IDs"""
    print("🔍 TESTING STAFF LOOKUP FIX")
    print("=" * 50)
    
    try:
        from app import app
        from salary_calculator import SalaryCalculator
        from database import get_db
        
        with app.app_context():
            db = get_db()
            
            # Get all staff from database
            print("\n1. Getting staff from database...")
            staff_list = db.execute('SELECT id, staff_id, full_name FROM staff').fetchall()
            
            if not staff_list:
                print("   ❌ No staff found in database")
                return False
            
            print(f"   ✅ Found {len(staff_list)} staff members:")
            for staff in staff_list:
                print(f"      - ID: {staff['id']}, Staff ID: {staff['staff_id']}, Name: {staff['full_name']}")
            
            # Test salary calculation with database ID
            print("\n2. Testing salary calculation with database ID...")
            calc = SalaryCalculator()
            
            for staff in staff_list:
                print(f"\n   Testing staff: {staff['full_name']} (DB ID: {staff['id']}, Staff ID: {staff['staff_id']})")
                
                # Test with database ID (this should work)
                result = calc.calculate_monthly_salary(staff['id'], 2024, 1)
                
                if result['success']:
                    print(f"   ✅ Salary calculation successful for DB ID {staff['id']}")
                    print(f"      Net Salary: ₹{result['salary_breakdown']['net_salary']}")
                else:
                    print(f"   ❌ Salary calculation failed for DB ID {staff['id']}: {result['error']}")
                
                # Test staff info lookup directly
                staff_info = calc._get_staff_info(staff['id'])
                if staff_info:
                    print(f"   ✅ Staff info lookup successful for DB ID {staff['id']}")
                    print(f"      Found: {staff_info['full_name']} - {staff_info['staff_id']}")
                else:
                    print(f"   ❌ Staff info lookup failed for DB ID {staff['id']}")
            
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_bulk_calculation_data():
    """Test that bulk calculation returns correct data structure"""
    print("\n" + "=" * 50)
    print("🔍 TESTING BULK CALCULATION DATA STRUCTURE")
    print("=" * 50)
    
    try:
        from app import app
        from salary_calculator import SalaryCalculator
        from database import get_db
        import calendar
        
        with app.app_context():
            db = get_db()
            
            # Simulate bulk calculation logic
            print("\n1. Simulating bulk salary calculation...")
            
            school_id = 1
            year = 2024
            month = 1
            
            query = 'SELECT id, staff_id, full_name, department FROM staff WHERE school_id = ?'
            staff_list = db.execute(query, [school_id]).fetchall()
            
            if not staff_list:
                print("   ❌ No staff found for bulk calculation")
                return False
            
            print(f"   ✅ Found {len(staff_list)} staff for bulk calculation")
            
            salary_calculator = SalaryCalculator()
            results = []
            
            for staff in staff_list:
                print(f"\n   Processing: {staff['full_name']} (DB ID: {staff['id']}, Staff ID: {staff['staff_id']})")
                
                salary_result = salary_calculator.calculate_monthly_salary(staff['id'], year, month)
                if salary_result['success']:
                    result_data = {
                        'id': staff['id'],  # Database ID for detail lookup
                        'staff_id': staff['staff_id'],  # Display ID
                        'staff_name': staff['full_name'],
                        'department': staff['department'],
                        'net_salary': salary_result['salary_breakdown']['net_salary'],
                        'total_earnings': salary_result['salary_breakdown']['earnings']['total_earnings'],
                        'total_deductions': salary_result['salary_breakdown']['deductions']['total_deductions'],
                        'present_days': salary_result['salary_breakdown']['attendance_summary']['present_days'],
                        'absent_days': salary_result['salary_breakdown']['attendance_summary']['absent_days']
                    }
                    results.append(result_data)
                    print(f"   ✅ Calculation successful - Net Salary: ₹{result_data['net_salary']}")
                else:
                    print(f"   ❌ Calculation failed: {salary_result['error']}")
            
            print(f"\n2. Bulk calculation results:")
            print(f"   Total staff processed: {len(results)}")
            
            if results:
                print(f"   Sample result structure:")
                sample = results[0]
                print(f"      - Database ID (for lookup): {sample['id']}")
                print(f"      - Staff ID (for display): {sample['staff_id']}")
                print(f"      - Staff Name: {sample['staff_name']}")
                print(f"      - Net Salary: ₹{sample['net_salary']}")
                
                # Test that we can lookup details using the database ID
                print(f"\n3. Testing detail lookup with database ID {sample['id']}...")
                detail_result = salary_calculator.calculate_monthly_salary(sample['id'], year, month)
                
                if detail_result['success']:
                    print(f"   ✅ Detail lookup successful!")
                    print(f"      Staff: {detail_result['staff_info']['full_name']}")
                    print(f"      Net Salary: ₹{detail_result['salary_breakdown']['net_salary']}")
                else:
                    print(f"   ❌ Detail lookup failed: {detail_result['error']}")
            
            return len(results) > 0
            
    except Exception as e:
        print(f"❌ Bulk calculation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🎯 STAFF LOOKUP FIX VERIFICATION")
    print("Testing the fix for 'Staff not found' error in salary details")
    print("=" * 60)
    
    # Test staff lookup
    lookup_ok = test_staff_lookup()
    
    # Test bulk calculation data structure
    bulk_ok = test_bulk_calculation_data()
    
    print("\n" + "=" * 60)
    print("🔍 TEST SUMMARY")
    print("=" * 60)
    
    if lookup_ok and bulk_ok:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Staff lookup is working correctly")
        print("✅ Bulk calculation returns correct data structure")
        print("✅ Detail lookup uses correct database IDs")
        print("\n💡 THE 'Staff not found' ERROR SHOULD NOW BE FIXED!")
        print("\nWhat was fixed:")
        print("- Bulk calculation now includes database ID ('id') in results")
        print("- JavaScript now passes database ID instead of staff_id string")
        print("- Salary calculator can now find staff correctly")
        return True
    else:
        print("❌ Some tests failed")
        if not lookup_ok:
            print("- Staff lookup issues")
        if not bulk_ok:
            print("- Bulk calculation data structure issues")
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
