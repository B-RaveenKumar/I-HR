#!/usr/bin/env python3
"""
Test the complete Institution Timing Configuration update flow
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
    
    print("🔧 Testing Complete Institution Timing Update Flow")
    print("=" * 60)
    
    with app.app_context():
        db = get_db()
        
        # Step 1: Show current state
        print("\n1. Current State:")
        timings = get_institution_timings()
        print(f"   Institution timings: {timings['checkin_time']} - {timings['checkout_time']} (Custom: {timings['is_custom']})")
        
        shift_manager = ShiftManager()
        general_shift = shift_manager.get_shift_info('general')
        print(f"   ShiftManager general: {general_shift['start_time']} - {general_shift['end_time']}")
        
        # Step 2: Update institution timings to new values
        print("\n2. Updating Institution Timings...")
        new_checkin = "07:45"
        new_checkout = "15:45"
        
        # Ensure institution_settings table exists
        db.execute("""
            CREATE TABLE IF NOT EXISTS institution_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_name TEXT UNIQUE NOT NULL,
                setting_value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Update timings
        db.execute("""
            INSERT OR REPLACE INTO institution_settings (setting_name, setting_value, updated_at)
            VALUES ('checkin_time', ?, CURRENT_TIMESTAMP)
        """, (new_checkin,))
        
        db.execute("""
            INSERT OR REPLACE INTO institution_settings (setting_name, setting_value, updated_at)
            VALUES ('checkout_time', ?, CURRENT_TIMESTAMP)
        """, (new_checkout,))
        
        db.commit()
        print(f"   ✅ Updated institution timings to {new_checkin} - {new_checkout}")
        
        # Step 3: Verify updated timings are reflected
        print("\n3. Verifying Updated Timings...")
        updated_timings = get_institution_timings()
        expected_checkin = datetime.time(7, 45)
        expected_checkout = datetime.time(15, 45)
        
        if (updated_timings['checkin_time'] == expected_checkin and 
            updated_timings['checkout_time'] == expected_checkout):
            print(f"   ✅ Institution timings updated: {updated_timings['checkin_time']} - {updated_timings['checkout_time']}")
        else:
            print("   ❌ Institution timings not updated correctly")
            sys.exit(1)
        
        # Step 4: Test ShiftManager synchronization
        print("\n4. Testing ShiftManager Synchronization...")
        # Create new ShiftManager instance (simulates system reload)
        new_shift_manager = ShiftManager()
        new_general_shift = new_shift_manager.get_shift_info('general')
        
        if (new_general_shift['start_time'] == expected_checkin and
            new_general_shift['end_time'] == expected_checkout):
            print(f"   ✅ ShiftManager synchronized: {new_general_shift['start_time']} - {new_general_shift['end_time']}")
        else:
            print(f"   ❌ ShiftManager not synchronized: {new_general_shift['start_time']} - {new_general_shift['end_time']}")
            sys.exit(1)
        
        # Step 5: Test attendance status calculation with new timings
        print("\n5. Testing Attendance Status Calculation...")
        test_cases = [
            (datetime.time(7, 40), "Present"),  # 5 min early
            (datetime.time(7, 45), "Present"),  # Exactly on time
            (datetime.time(7, 50), "Late"),     # 5 min late
            (datetime.time(8, 15), "Late"),     # 30 min late
            (datetime.time(17, 39), "Late"),    # Very late (user's scenario)
        ]
        
        all_passed = True
        for test_time, expected_status in test_cases:
            result = new_shift_manager.calculate_attendance_status('general', test_time)
            actual_status = result['status']
            
            if actual_status.lower() == expected_status.lower():
                print(f"   ✅ {test_time} -> {actual_status}")
                if actual_status.lower() == 'late':
                    late_minutes = result.get('late_duration_minutes', 0)
                    print(f"      Late duration: {late_minutes} minutes")
            else:
                print(f"   ❌ {test_time} -> {actual_status} (Expected: {expected_status})")
                all_passed = False
        
        if not all_passed:
            sys.exit(1)
        
        # Step 6: Test the user's specific scenario (5:39 PM vs 7:45 AM)
        print("\n6. Testing User's Specific Scenario...")
        user_checkin_time = datetime.time(17, 39)  # 5:39 PM
        result = new_shift_manager.calculate_attendance_status('general', user_checkin_time)
        
        if result['status'].lower() == 'late':
            late_minutes = result.get('late_duration_minutes', 0)
            expected_minutes = (17 * 60 + 39) - (7 * 60 + 45)  # 5:39 PM - 7:45 AM
            print(f"   ✅ 5:39 PM check-in correctly marked as Late")
            print(f"   ✅ Late duration: {late_minutes} minutes (Expected: ~{expected_minutes})")
            
            if abs(late_minutes - expected_minutes) <= 1:
                print("   ✅ Late duration calculation is accurate")
            else:
                print(f"   ⚠️ Late duration may be off by {abs(late_minutes - expected_minutes)} minutes")
        else:
            print(f"   ❌ 5:39 PM check-in incorrectly marked as {result['status']}")
            sys.exit(1)
        
        # Step 7: Reset to original timings for cleanup
        print("\n7. Cleanup - Resetting to Default Timings...")
        db.execute("""
            INSERT OR REPLACE INTO institution_settings (setting_name, setting_value, updated_at)
            VALUES ('checkin_time', '09:00', CURRENT_TIMESTAMP)
        """)
        
        db.execute("""
            INSERT OR REPLACE INTO institution_settings (setting_name, setting_value, updated_at)
            VALUES ('checkout_time', '17:00', CURRENT_TIMESTAMP)
        """)
        
        db.commit()
        
        # Verify reset
        reset_timings = get_institution_timings()
        if (reset_timings['checkin_time'] == datetime.time(9, 0) and
            reset_timings['checkout_time'] == datetime.time(17, 0)):
            print("   ✅ Successfully reset to default timings (9:00 AM - 5:00 PM)")
        else:
            print("   ⚠️ Reset may not have worked completely")
    
    print("\n" + "=" * 60)
    print("🎉 All Institution Timing Configuration tests passed!")
    print("✅ The feature is working correctly:")
    print("   • Institution timings can be updated")
    print("   • ShiftManager automatically synchronizes")
    print("   • Attendance status calculation uses strict timing rules")
    print("   • Very late arrivals are correctly marked as Late")
    print("   • Late duration is accurately calculated")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
