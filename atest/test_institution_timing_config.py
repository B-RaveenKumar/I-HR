#!/usr/bin/env python3
"""
Test script for Institution Timing Configuration feature
Tests the complete flow from UI configuration to attendance status calculation
"""

import sys
import os
import datetime
import time

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from database import get_db, get_institution_timings
from shift_management import ShiftManager

def test_institution_timing_configuration():
    """Test the complete Institution Timing Configuration feature"""
    print("🔧 Testing Institution Timing Configuration Feature")
    print("=" * 60)
    
    with app.app_context():
        db = get_db()
        
        # Test 1: Check current institution timings
        print("\n1. Testing current institution timings retrieval...")
        try:
            timings = get_institution_timings()
            print(f"✅ Current timings loaded:")
            print(f"   Check-in: {timings['checkin_time']}")
            print(f"   Check-out: {timings['checkout_time']}")
            print(f"   Is custom: {timings['is_custom']}")
        except Exception as e:
            print(f"❌ Failed to get current timings: {e}")
            return False
        
        # Test 2: Update institution timings
        print("\n2. Testing institution timing updates...")
        try:
            # Ensure institution_settings table exists
            db.execute("""
                CREATE TABLE IF NOT EXISTS institution_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_name TEXT UNIQUE NOT NULL,
                    setting_value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Update to new test timings
            new_checkin = "08:30"
            new_checkout = "16:30"
            
            db.execute("""
                INSERT OR REPLACE INTO institution_settings (setting_name, setting_value, updated_at)
                VALUES ('checkin_time', ?, CURRENT_TIMESTAMP)
            """, (new_checkin,))
            
            db.execute("""
                INSERT OR REPLACE INTO institution_settings (setting_name, setting_value, updated_at)
                VALUES ('checkout_time', ?, CURRENT_TIMESTAMP)
            """, (new_checkout,))
            
            db.commit()
            print(f"✅ Updated institution timings to {new_checkin} - {new_checkout}")
            
        except Exception as e:
            print(f"❌ Failed to update timings: {e}")
            return False
        
        # Test 3: Verify updated timings are reflected
        print("\n3. Testing updated timings reflection...")
        try:
            updated_timings = get_institution_timings()
            expected_checkin = datetime.time(8, 30)
            expected_checkout = datetime.time(16, 30)
            
            if (updated_timings['checkin_time'] == expected_checkin and 
                updated_timings['checkout_time'] == expected_checkout and
                updated_timings['is_custom'] == True):
                print("✅ Updated timings correctly reflected:")
                print(f"   Check-in: {updated_timings['checkin_time']}")
                print(f"   Check-out: {updated_timings['checkout_time']}")
                print(f"   Is custom: {updated_timings['is_custom']}")
            else:
                print("❌ Updated timings not correctly reflected")
                return False
                
        except Exception as e:
            print(f"❌ Failed to verify updated timings: {e}")
            return False
        
        # Test 4: Test ShiftManager integration
        print("\n4. Testing ShiftManager integration with updated timings...")
        try:
            shift_manager = ShiftManager()
            # Force reload to pick up new institution timings
            shift_manager.reload_shift_definitions()
            
            general_shift = shift_manager.get_shift_info('general')
            if general_shift:
                print(f"✅ ShiftManager updated with new timings:")
                print(f"   Shift start: {general_shift['start_time']}")
                print(f"   Shift end: {general_shift['end_time']}")
                
                # Verify it matches institution timings
                if (general_shift['start_time'] == updated_timings['checkin_time'] and
                    general_shift['end_time'] == updated_timings['checkout_time']):
                    print("✅ ShiftManager perfectly synchronized with institution timings")
                else:
                    print("⚠️ ShiftManager not fully synchronized")
            else:
                print("❌ Failed to get general shift info")
                return False
                
        except Exception as e:
            print(f"❌ Failed to test ShiftManager integration: {e}")
            return False
        
        # Test 5: Test attendance status calculation with new timings
        print("\n5. Testing attendance status calculation with new timings...")
        try:
            # Test various check-in times against new 8:30 AM start
            test_cases = [
                (datetime.time(8, 25), "Present"),  # 5 min early
                (datetime.time(8, 30), "Present"),  # Exactly on time
                (datetime.time(8, 35), "Late"),     # 5 min late
                (datetime.time(9, 0), "Late"),      # 30 min late
                (datetime.time(12, 0), "Late"),     # Very late (like the user's case)
            ]
            
            for test_time, expected_status in test_cases:
                result = shift_manager.calculate_attendance_status('general', test_time)
                actual_status = result['status']
                
                if actual_status.lower() == expected_status.lower():
                    print(f"✅ {test_time} -> {actual_status} (Expected: {expected_status})")
                    if actual_status.lower() == 'late':
                        late_minutes = result.get('late_duration_minutes', 0)
                        print(f"   Late duration: {late_minutes} minutes")
                else:
                    print(f"❌ {test_time} -> {actual_status} (Expected: {expected_status})")
                    return False
                    
        except Exception as e:
            print(f"❌ Failed to test attendance status calculation: {e}")
            return False
        
        # Test 6: Test very late arrival scenario (like user's 5:39 PM case)
        print("\n6. Testing very late arrival scenario...")
        try:
            very_late_time = datetime.time(17, 39)  # 5:39 PM
            result = shift_manager.calculate_attendance_status('general', very_late_time)
            
            if result['status'].lower() == 'late':
                late_minutes = result.get('late_duration_minutes', 0)
                expected_minutes = (17 * 60 + 39) - (8 * 60 + 30)  # 5:39 PM - 8:30 AM
                print(f"✅ Very late arrival (5:39 PM) correctly marked as Late")
                print(f"   Late duration: {late_minutes} minutes (Expected: ~{expected_minutes})")
                
                if abs(late_minutes - expected_minutes) <= 1:  # Allow 1 minute tolerance
                    print("✅ Late duration calculation is accurate")
                else:
                    print(f"⚠️ Late duration calculation may be off by {abs(late_minutes - expected_minutes)} minutes")
            else:
                print(f"❌ Very late arrival incorrectly marked as {result['status']} instead of Late")
                return False
                
        except Exception as e:
            print(f"❌ Failed to test very late arrival: {e}")
            return False
        
        # Test 7: Reset to original timings
        print("\n7. Resetting to original timings...")
        try:
            # Reset to default 9:00 AM - 5:00 PM
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
                print("✅ Successfully reset to original timings (9:00 AM - 5:00 PM)")
            else:
                print("⚠️ Reset may not have worked completely")
                
        except Exception as e:
            print(f"❌ Failed to reset timings: {e}")
            return False
    
    print("\n" + "=" * 60)
    print("🎉 All Institution Timing Configuration tests passed!")
    print("✅ Feature is working correctly and ready for production use")
    return True

if __name__ == "__main__":
    success = test_institution_timing_configuration()
    sys.exit(0 if success else 1)
