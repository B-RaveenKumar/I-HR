#!/usr/bin/env python3
"""
Simple test for Institution Timing Configuration
"""

import sys
import os
import datetime

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app import app
    from database import get_db, get_institution_timings
    from shift_management import ShiftManager
    
    print("✅ All imports successful")
    
    with app.app_context():
        print("\n🔧 Testing Institution Timing Configuration...")
        
        # Test 1: Get current timings
        timings = get_institution_timings()
        print(f"Current timings: {timings['checkin_time']} - {timings['checkout_time']} (Custom: {timings['is_custom']})")
        
        # Test 2: Test ShiftManager
        shift_manager = ShiftManager()
        general_shift = shift_manager.get_shift_info('general')
        if general_shift:
            print(f"ShiftManager general shift: {general_shift['start_time']} - {general_shift['end_time']}")
        
        # Test 3: Test attendance calculation
        test_time = datetime.time(9, 30)  # 9:30 AM
        result = shift_manager.calculate_attendance_status('general', test_time)
        print(f"9:30 AM check-in status: {result['status']}")
        
        # Test 4: Test very late arrival
        very_late_time = datetime.time(17, 39)  # 5:39 PM
        result = shift_manager.calculate_attendance_status('general', very_late_time)
        print(f"5:39 PM check-in status: {result['status']}")
        if result['status'] == 'late':
            print(f"Late duration: {result.get('late_duration_minutes', 0)} minutes")
        
        print("\n✅ Basic functionality test completed")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
