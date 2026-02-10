#!/usr/bin/env python3
"""Test script to verify the calendar fix for sqlite3.Row object access"""

import sqlite3
import datetime
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import calculate_daily_attendance_data, format_time_to_12hr

# Test the sqlite3.Row access fix
class TestRow:
    """Mock sqlite3.Row object for testing"""
    def __init__(self, data):
        self._data = data
    
    def __getitem__(self, key):
        return self._data[key]
    
    def keys(self):
        return self._data.keys()

def test_calendar_function():
    """Test the calendar function with mock data"""
    
    # Create test data that mimics sqlite3.Row objects
    test_attendance = TestRow({
        'status': 'present',
        'time_in': '09:00:00',
        'time_out': '17:30:00',
        'late_duration_minutes': 0,
        'early_departure_minutes': 0,
        'on_duty_type': None,
        'on_duty_location': None,
        'on_duty_purpose': None
    })

    test_shift = TestRow({
        'start_time': '09:00:00',
        'end_time': '17:00:00',
        'grace_period_minutes': 10
    })

    # Test the function
    try:
        result = calculate_daily_attendance_data(
            datetime.date.today(),
            test_attendance,
            test_shift,
            'general'
        )
        print('✅ Function executed successfully!')
        print('Present Status:', result['present_status'])
        print('Morning Thumb:', result['morning_thumb'])
        print('Evening Thumb:', result['evening_thumb'])
        print('Shift Start Time:', result['shift_start_time'])
        print('Shift End Time:', result['shift_end_time'])
        return True
    except Exception as e:
        print('❌ Error:', str(e))
        import traceback
        traceback.print_exc()
        return False

def test_on_duty_status():
    """Test the on-duty status handling"""
    
    test_attendance = TestRow({
        'status': 'on_duty',
        'time_in': None,
        'time_out': None,
        'late_duration_minutes': None,
        'early_departure_minutes': None,
        'on_duty_type': 'Meeting',
        'on_duty_location': 'Main Office',
        'on_duty_purpose': 'Client presentation'
    })

    test_shift = TestRow({
        'start_time': '09:00:00',
        'end_time': '17:00:00',
        'grace_period_minutes': 10
    })

    try:
        result = calculate_daily_attendance_data(
            datetime.date.today(),
            test_attendance,
            test_shift,
            'general'
        )
        print('\n✅ On-duty test executed successfully!')
        print('Present Status:', result['present_status'])
        print('On Duty Type:', result['on_duty_type'])
        print('On Duty Location:', result['on_duty_location'])
        print('On Duty Purpose:', result['on_duty_purpose'])
        return True
    except Exception as e:
        print('\n❌ On-duty test error:', str(e))
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("Testing calendar function fixes...")
    
    success1 = test_calendar_function()
    success2 = test_on_duty_status()
    
    if success1 and success2:
        print('\n🎉 All tests passed! The sqlite3.Row access issue has been fixed.')
    else:
        print('\n💥 Some tests failed. Please check the error messages above.')
