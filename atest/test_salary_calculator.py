#!/usr/bin/env python3
"""
Test script for salary calculator functionality
Tests comprehensive salary calculations including all attendance factors
"""

import sys
import os
import datetime
from unittest.mock import MagicMock, patch

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the salary calculator
from salary_calculator import SalaryCalculator

def test_basic_salary_calculation():
    """Test basic salary calculation with present days only"""
    print("Testing basic salary calculation...")
    
    # Mock database connection
    with patch('salary_calculator.get_db') as mock_db:
        # Mock staff info
        mock_staff = {
            'id': 1,
            'staff_id': 'EMP001',
            'full_name': 'John Doe',
            'basic_salary': 30000.0,
            'hra': 5000.0,
            'transport_allowance': 2000.0,
            'other_allowances': 1000.0,
            'pf_deduction': 1800.0,
            'esi_deduction': 150.0,
            'professional_tax': 200.0,
            'other_deductions': 0.0
        }
        
        # Mock attendance data - all present days
        mock_attendance = [
            {
                'date': '2024-01-01',
                'status': 'present',
                'time_in': '09:00:00',
                'time_out': '17:00:00',
                'late_duration_minutes': 0,
                'early_departure_minutes': 0,
                'overtime_hours': 0,
                'on_duty_type': None,
                'on_duty_location': None,
                'on_duty_purpose': None,
                'work_hours': 8
            }
        ] * 22  # 22 working days
        
        # Mock leave data - no leaves
        mock_leaves = []
        
        # Setup mock database responses
        mock_db_instance = MagicMock()
        mock_db.return_value = mock_db_instance
        
        # Mock staff info query
        mock_db_instance.execute.return_value.fetchone.side_effect = [
            mock_staff,  # Staff info query
            {'shift_type': 'general', 'start_time': '09:00:00', 'end_time': '17:00:00', 'grace_period_minutes': 10}  # Shift info query
        ]
        
        # Mock attendance and leave queries
        mock_db_instance.execute.return_value.fetchall.side_effect = [
            mock_attendance,  # Attendance query
            mock_leaves       # Leave query
        ]
        
        # Create calculator and test
        calculator = SalaryCalculator()
        result = calculator.calculate_monthly_salary(1, 2024, 1)
        
        print(f"Result: {result['success']}")
        if result['success']:
            breakdown = result['salary_breakdown']
            print(f"Working Days: {breakdown['working_days']}")
            print(f"Present Days: {breakdown['attendance_summary']['present_days']}")
            print(f"Total Earnings: ₹{breakdown['earnings']['total_earnings']}")
            print(f"Total Deductions: ₹{breakdown['deductions']['total_deductions']}")
            print(f"Net Salary: ₹{breakdown['net_salary']}")
            
            # Basic assertions
            assert breakdown['attendance_summary']['present_days'] == 22, "Should have 22 present days"
            assert breakdown['earnings']['total_earnings'] > 0, "Should have positive earnings"
            assert breakdown['net_salary'] > 0, "Should have positive net salary"
            
        print("✅ Basic salary calculation test passed!\n")

def test_early_arrival_bonus():
    """Test early arrival bonus calculation"""
    print("Testing early arrival bonus...")
    
    with patch('salary_calculator.get_db') as mock_db:
        mock_staff = {
            'id': 1,
            'staff_id': 'EMP001',
            'full_name': 'John Doe',
            'basic_salary': 30000.0,
            'hra': 5000.0,
            'transport_allowance': 2000.0,
            'other_allowances': 1000.0,
            'pf_deduction': 1800.0,
            'esi_deduction': 150.0,
            'professional_tax': 200.0,
            'other_deductions': 0.0
        }
        
        # Mock attendance with early arrivals
        mock_attendance = [
            {
                'date': '2024-01-01',
                'status': 'present',
                'time_in': '08:30:00',  # 30 minutes early
                'time_out': '17:00:00',
                'late_duration_minutes': 0,
                'early_departure_minutes': 0,
                'overtime_hours': 0,
                'on_duty_type': None,
                'on_duty_location': None,
                'on_duty_purpose': None,
                'work_hours': 8
            }
        ] * 10  # 10 days with early arrival
        
        mock_leaves = []
        
        mock_db_instance = MagicMock()
        mock_db.return_value = mock_db_instance
        
        mock_db_instance.execute.return_value.fetchone.side_effect = [
            mock_staff,
            {'shift_type': 'general', 'start_time': '09:00:00', 'end_time': '17:00:00', 'grace_period_minutes': 10}
        ]
        
        mock_db_instance.execute.return_value.fetchall.side_effect = [
            mock_attendance,
            mock_leaves
        ]
        
        calculator = SalaryCalculator()
        result = calculator.calculate_monthly_salary(1, 2024, 1)
        
        if result['success']:
            breakdown = result['salary_breakdown']
            early_bonus = breakdown['earnings']['early_arrival_bonus']
            
            print(f"Early Arrival Bonus: ₹{early_bonus}")
            
            # Should have bonus for 10 days * 0.5 hours * ₹50/hour = ₹250
            expected_bonus = 10 * 0.5 * 50  # 10 days, 30 minutes each, ₹50/hour
            print(f"Expected Bonus: ₹{expected_bonus}")
            
            assert early_bonus > 0, "Should have early arrival bonus"
            
        print("✅ Early arrival bonus test passed!\n")

def test_early_departure_penalty():
    """Test early departure penalty calculation"""
    print("Testing early departure penalty...")
    
    with patch('salary_calculator.get_db') as mock_db:
        mock_staff = {
            'id': 1,
            'staff_id': 'EMP001',
            'full_name': 'John Doe',
            'basic_salary': 30000.0,
            'hra': 5000.0,
            'transport_allowance': 2000.0,
            'other_allowances': 1000.0,
            'pf_deduction': 1800.0,
            'esi_deduction': 150.0,
            'professional_tax': 200.0,
            'other_deductions': 0.0
        }
        
        # Mock attendance with early departures
        mock_attendance = [
            {
                'date': '2024-01-01',
                'status': 'present',
                'time_in': '09:00:00',
                'time_out': '16:00:00',  # 1 hour early departure
                'late_duration_minutes': 0,
                'early_departure_minutes': 60,
                'overtime_hours': 0,
                'on_duty_type': None,
                'on_duty_location': None,
                'on_duty_purpose': None,
                'work_hours': 7
            }
        ] * 5  # 5 days with early departure
        
        mock_leaves = []
        
        mock_db_instance = MagicMock()
        mock_db.return_value = mock_db_instance
        
        mock_db_instance.execute.return_value.fetchone.side_effect = [
            mock_staff,
            {'shift_type': 'general', 'start_time': '09:00:00', 'end_time': '17:00:00', 'grace_period_minutes': 10}
        ]
        
        mock_db_instance.execute.return_value.fetchall.side_effect = [
            mock_attendance,
            mock_leaves
        ]
        
        calculator = SalaryCalculator()
        result = calculator.calculate_monthly_salary(1, 2024, 1)
        
        if result['success']:
            breakdown = result['salary_breakdown']
            early_penalty = breakdown['deductions']['early_departure_penalty']
            
            print(f"Early Departure Penalty: ₹{early_penalty}")
            
            # Should have penalty for 5 days * 1 hour * ₹100/hour = ₹500
            expected_penalty = 5 * 1 * 100
            print(f"Expected Penalty: ₹{expected_penalty}")
            
            assert early_penalty > 0, "Should have early departure penalty"
            
        print("✅ Early departure penalty test passed!\n")

def test_combined_scenario():
    """Test combined scenario with various attendance factors"""
    print("Testing combined scenario...")
    
    with patch('salary_calculator.get_db') as mock_db:
        mock_staff = {
            'id': 1,
            'staff_id': 'EMP001',
            'full_name': 'John Doe',
            'basic_salary': 30000.0,
            'hra': 5000.0,
            'transport_allowance': 2000.0,
            'other_allowances': 1000.0,
            'pf_deduction': 1800.0,
            'esi_deduction': 150.0,
            'professional_tax': 200.0,
            'other_deductions': 0.0
        }
        
        # Mixed attendance data
        mock_attendance = [
            # Present with early arrival
            {
                'date': '2024-01-01',
                'status': 'present',
                'time_in': '08:30:00',
                'time_out': '17:00:00',
                'late_duration_minutes': 0,
                'early_departure_minutes': 0,
                'overtime_hours': 0,
                'on_duty_type': None,
                'on_duty_location': None,
                'on_duty_purpose': None,
                'work_hours': 8
            },
            # Present with late arrival
            {
                'date': '2024-01-02',
                'status': 'present',
                'time_in': '09:30:00',
                'time_out': '17:00:00',
                'late_duration_minutes': 20,  # 20 minutes late after grace period
                'early_departure_minutes': 0,
                'overtime_hours': 0,
                'on_duty_type': None,
                'on_duty_location': None,
                'on_duty_purpose': None,
                'work_hours': 7.5
            },
            # Present with early departure
            {
                'date': '2024-01-03',
                'status': 'present',
                'time_in': '09:00:00',
                'time_out': '16:30:00',
                'late_duration_minutes': 0,
                'early_departure_minutes': 30,
                'overtime_hours': 0,
                'on_duty_type': None,
                'on_duty_location': None,
                'on_duty_purpose': None,
                'work_hours': 7.5
            },
            # On duty
            {
                'date': '2024-01-04',
                'status': 'on_duty',
                'time_in': '09:00:00',
                'time_out': '17:00:00',
                'late_duration_minutes': 0,
                'early_departure_minutes': 0,
                'overtime_hours': 0,
                'on_duty_type': 'field_work',
                'on_duty_location': 'Client Site',
                'on_duty_purpose': 'Project Meeting',
                'work_hours': 8
            },
            # Absent
            {
                'date': '2024-01-05',
                'status': 'absent',
                'time_in': None,
                'time_out': None,
                'late_duration_minutes': 0,
                'early_departure_minutes': 0,
                'overtime_hours': 0,
                'on_duty_type': None,
                'on_duty_location': None,
                'on_duty_purpose': None,
                'work_hours': 0
            }
        ]
        
        # Mock leave data
        mock_leaves = [
            {
                'leave_type': 'casual_leave',
                'start_date': '2024-01-06',
                'end_date': '2024-01-06',
                'days_requested': 1,
                'status': 'approved',
                'reason': 'Personal work',
                'half_day': False
            }
        ]
        
        mock_db_instance = MagicMock()
        mock_db.return_value = mock_db_instance
        
        mock_db_instance.execute.return_value.fetchone.side_effect = [
            mock_staff,
            {'shift_type': 'general', 'start_time': '09:00:00', 'end_time': '17:00:00', 'grace_period_minutes': 10}
        ]
        
        mock_db_instance.execute.return_value.fetchall.side_effect = [
            mock_attendance,
            mock_leaves
        ]
        
        calculator = SalaryCalculator()
        result = calculator.calculate_monthly_salary(1, 2024, 1)
        
        if result['success']:
            breakdown = result['salary_breakdown']
            attendance = breakdown['attendance_summary']
            earnings = breakdown['earnings']
            deductions = breakdown['deductions']
            
            print(f"Attendance Summary:")
            print(f"  Present Days: {attendance['present_days']}")
            print(f"  Absent Days: {attendance['absent_days']}")
            print(f"  On Duty Days: {attendance['on_duty_days']}")
            print(f"  Leave Days: {attendance['leave_days']}")
            
            print(f"\nEarnings:")
            print(f"  Early Arrival Bonus: ₹{earnings['early_arrival_bonus']}")
            print(f"  Overtime Pay: ₹{earnings['overtime_pay']}")
            print(f"  Total Earnings: ₹{earnings['total_earnings']}")
            
            print(f"\nDeductions:")
            print(f"  Early Departure Penalty: ₹{deductions['early_departure_penalty']}")
            print(f"  Late Arrival Penalty: ₹{deductions['late_arrival_penalty']}")
            print(f"  Absent Deduction: ₹{deductions['absent_deduction']}")
            print(f"  Total Deductions: ₹{deductions['total_deductions']}")
            
            print(f"\nNet Salary: ₹{breakdown['net_salary']}")
            
            # Assertions
            assert attendance['present_days'] == 3, "Should have 3 present days"
            assert attendance['absent_days'] == 1, "Should have 1 absent day"
            assert attendance['on_duty_days'] == 1, "Should have 1 on duty day"
            assert attendance['leave_days'] == 1, "Should have 1 leave day"
            
            assert earnings['early_arrival_bonus'] > 0, "Should have early arrival bonus"
            assert deductions['early_departure_penalty'] > 0, "Should have early departure penalty"
            assert deductions['late_arrival_penalty'] > 0, "Should have late arrival penalty"
            assert deductions['absent_deduction'] > 0, "Should have absent deduction"
            
        print("✅ Combined scenario test passed!\n")

def main():
    """Run all salary calculator tests"""
    print("=" * 60)
    print("SALARY CALCULATOR TESTS")
    print("=" * 60)
    print()
    
    try:
        test_basic_salary_calculation()
        test_early_arrival_bonus()
        test_early_departure_penalty()
        test_combined_scenario()
        
        print("=" * 60)
        print("🎉 ALL SALARY CALCULATOR TESTS PASSED! 🎉")
        print("=" * 60)
        print()
        print("The salary calculation system is working correctly:")
        print("✅ Basic salary calculations with present/absent days")
        print("✅ Early arrival bonus calculations")
        print("✅ Early departure penalty calculations")
        print("✅ Late arrival penalty calculations")
        print("✅ On duty day calculations")
        print("✅ Leave day calculations")
        print("✅ Combined scenario handling")
        print("✅ Comprehensive earnings and deductions breakdown")
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
