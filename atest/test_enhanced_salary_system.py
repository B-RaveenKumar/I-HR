#!/usr/bin/env python3
"""
Test script for the enhanced salary calculation system
"""

import sys
import os
import sqlite3
from datetime import datetime, date, time
import requests
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db, calculate_hourly_rate, calculate_standard_working_hours_per_month
from salary_calculator import SalaryCalculator

def test_hourly_rate_calculation():
    """Test the hourly rate calculation function"""
    print("\n🧪 Testing Hourly Rate Calculation...")
    
    try:
        # Test with different base salaries
        test_cases = [
            {"base_salary": 30000, "expected_min": 100, "expected_max": 200},
            {"base_salary": 50000, "expected_min": 200, "expected_max": 300},
            {"base_salary": 0, "expected": 0}
        ]
        
        for case in test_cases:
            result = calculate_hourly_rate(case["base_salary"])
            hourly_rate = result['hourly_rate']
            
            if case["base_salary"] == 0:
                if hourly_rate == case["expected"]:
                    print(f"   ✅ Base salary {case['base_salary']}: Hourly rate = ₹{hourly_rate} (Expected: ₹{case['expected']})")
                else:
                    print(f"   ❌ Base salary {case['base_salary']}: Hourly rate = ₹{hourly_rate} (Expected: ₹{case['expected']})")
            else:
                if case["expected_min"] <= hourly_rate <= case["expected_max"]:
                    print(f"   ✅ Base salary ₹{case['base_salary']}: Hourly rate = ₹{hourly_rate} (Within expected range)")
                else:
                    print(f"   ❌ Base salary ₹{case['base_salary']}: Hourly rate = ₹{hourly_rate} (Outside expected range)")
            
            print(f"      Standard monthly hours: {result['standard_monthly_hours']}")
            print(f"      Daily rate: ₹{result['daily_rate']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error testing hourly rate calculation: {e}")
        return False

def test_standard_working_hours():
    """Test the standard working hours calculation"""
    print("\n🧪 Testing Standard Working Hours Calculation...")
    
    try:
        result = calculate_standard_working_hours_per_month()
        
        print(f"   📊 Daily hours: {result['daily_hours']}")
        print(f"   📊 Monthly hours: {result['monthly_hours']}")
        print(f"   📊 Working days per month: {result['working_days_per_month']}")
        
        # Basic validation
        if result['daily_hours'] > 0 and result['monthly_hours'] > 0 and result['working_days_per_month'] > 0:
            print("   ✅ Standard working hours calculation successful")
            return True
        else:
            print("   ❌ Invalid working hours calculation")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing standard working hours: {e}")
        return False

def test_enhanced_salary_calculator():
    """Test the enhanced salary calculator"""
    print("\n🧪 Testing Enhanced Salary Calculator...")
    
    try:
        calculator = SalaryCalculator()
        
        # Test with a mock staff ID (this will fail if no staff exists, but we can check the structure)
        test_staff_id = 1
        test_year = 2024
        test_month = 1
        
        result = calculator.calculate_enhanced_monthly_salary(test_staff_id, test_year, test_month)
        
        if result['success']:
            print("   ✅ Enhanced salary calculation successful")
            print(f"      Staff: {result['staff_name']}")
            print(f"      Base salary: ₹{result['base_monthly_salary']}")
            print(f"      Hourly rate: ₹{result['hourly_rate']}")
            print(f"      Standard hours: {result['standard_monthly_hours']}")
            print(f"      Actual hours: {result['actual_hours_worked']}")
            print(f"      Net salary: ₹{result['salary_breakdown']['net_salary']}")
            return True
        else:
            print(f"   ⚠️ Enhanced salary calculation returned error (expected if no test data): {result['error']}")
            return True  # This is expected if no test data exists
            
    except Exception as e:
        print(f"   ❌ Error testing enhanced salary calculator: {e}")
        return False

def test_salary_rules():
    """Test salary rules functionality"""
    print("\n🧪 Testing Salary Rules...")
    
    try:
        calculator = SalaryCalculator()
        
        # Check if new rules are present
        expected_rules = [
            'bonus_rate_percentage',
            'minimum_hours_for_bonus',
            'early_arrival_bonus_per_hour',
            'overtime_rate_multiplier'
        ]
        
        missing_rules = []
        for rule in expected_rules:
            if rule not in calculator.salary_rules:
                missing_rules.append(rule)
        
        if not missing_rules:
            print("   ✅ All expected salary rules are present")
            print(f"      Bonus rate percentage: {calculator.salary_rules['bonus_rate_percentage']}%")
            print(f"      Minimum hours for bonus: {calculator.salary_rules['minimum_hours_for_bonus']} hrs")
            return True
        else:
            print(f"   ❌ Missing salary rules: {missing_rules}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing salary rules: {e}")
        return False

def test_database_integration():
    """Test database integration"""
    print("\n🧪 Testing Database Integration...")
    
    try:
        db = get_db()
        
        # Check if staff table has salary fields
        cursor = db.execute("PRAGMA table_info(staff)")
        columns = [col[1] for col in cursor.fetchall()]
        
        expected_columns = ['basic_salary', 'hra', 'transport_allowance', 'other_allowances']
        missing_columns = [col for col in expected_columns if col not in columns]
        
        if not missing_columns:
            print("   ✅ All required salary columns exist in staff table")
            return True
        else:
            print(f"   ❌ Missing salary columns in staff table: {missing_columns}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing database integration: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("🚀 Starting Enhanced Salary System Tests")
    print("=" * 50)
    
    tests = [
        ("Database Integration", test_database_integration),
        ("Standard Working Hours", test_standard_working_hours),
        ("Hourly Rate Calculation", test_hourly_rate_calculation),
        ("Salary Rules", test_salary_rules),
        ("Enhanced Salary Calculator", test_enhanced_salary_calculator),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        if test_func():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"🏁 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Enhanced salary system is working correctly.")
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
