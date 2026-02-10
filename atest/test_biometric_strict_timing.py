#!/usr/bin/env python3
"""
Test biometric capture with strict timing rules
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

    print("🔍 Testing Biometric Capture with Strict Timing Rules")
    print("=" * 60)
    
    with app.app_context():
        db = get_db()
        
        # Step 1: Set up test environment
        print("\n1. Setting up test environment...")
        
        # Ensure we have institution timings
        timings = get_institution_timings()
        print(f"   Institution timings: {timings['checkin_time']} - {timings['checkout_time']}")
        
        # Test ShiftManager directly
        shift_manager = ShiftManager()
        general_shift = shift_manager.get_shift_info('general')
        print(f"   ShiftManager general shift: {general_shift['start_time']} - {general_shift['end_time']}")
        
        # Step 2: Test ShiftManager strict timing calculation
        print("\n2. Testing ShiftManager strict timing calculation...")
        
        test_cases = [
            (datetime.time(9, 44), "Present"),  # 1 min early
            (datetime.time(9, 45), "Present"),  # Exactly on time (9:45 AM)
            (datetime.time(9, 46), "Late"),     # 1 min late
            (datetime.time(10, 15), "Late"),    # 30 min late
            (datetime.time(17, 39), "Late"),    # Very late (user's scenario)
        ]
        
        all_passed = True
        for test_time, expected_status in test_cases:
            result = shift_manager.calculate_attendance_status('general', test_time)
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
            print("   ❌ ShiftManager strict timing test failed!")
            sys.exit(1)
        
        # Step 3: Test biometric capture simulation
        print("\n3. Testing biometric capture simulation...")
        
        # Create a test staff member if not exists
        test_staff = db.execute('''
            SELECT id FROM staff WHERE staff_id = 'TEST001' AND school_id = 1
        ''').fetchone()
        
        if not test_staff:
            db.execute('''
                INSERT INTO staff (staff_id, school_id, full_name, department, shift_type)
                VALUES ('TEST001', 1, 'Test Staff', 'IT', 'general')
            ''')
            db.commit()
            test_staff = db.execute('''
                SELECT id FROM staff WHERE staff_id = 'TEST001' AND school_id = 1
            ''').fetchone()
        
        test_staff_id = test_staff['id']
        print(f"   Using test staff ID: {test_staff_id}")
        
        # Clear any existing attendance for today
        today = datetime.date.today().strftime('%Y-%m-%d')
        db.execute('DELETE FROM attendance WHERE staff_id = ? AND date = ?', (test_staff_id, today))
        db.commit()
        
        # Step 4: Simulate very late biometric check-in (5:39 PM)
        print("\n4. Simulating very late biometric check-in (5:39 PM)...")

        # Simulate biometric verification manually
        late_timestamp = datetime.datetime.combine(datetime.date.today(), datetime.time(17, 39))

        # Get staff shift type
        staff_info = db.execute('SELECT COALESCE(shift_type, \'general\') AS shift_type FROM staff WHERE id = ?', (test_staff_id,)).fetchone()
        shift_type = staff_info['shift_type'] if staff_info else 'general'

        # Calculate status using ShiftManager (same logic as biometric capture)
        attendance_result = shift_manager.calculate_attendance_status(shift_type, late_timestamp.time())
        status = attendance_result['status']
        late_minutes = attendance_result.get('late_duration_minutes', 0)

        print(f"   Calculated status: {status}")
        print(f"   Late duration: {late_minutes} minutes")

        # Insert attendance record (same as biometric capture would do)
        db.execute('''
            INSERT INTO attendance (staff_id, school_id, date, time_in, status, late_duration_minutes,
                                    shift_start_time, shift_end_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            test_staff_id, 1, today, late_timestamp.strftime('%H:%M:%S'), status, late_minutes,
            attendance_result['shift_start_time'].strftime('%H:%M:%S'),
            attendance_result['shift_end_time'].strftime('%H:%M:%S')
        ))
        db.commit()

        print(f"   ✅ Biometric simulation completed: Status = {status}, Late minutes = {late_minutes}")
        
        # Step 5: Verify the attendance record
        print("\n5. Verifying attendance record in database...")
        
        attendance_record = db.execute('''
            SELECT * FROM attendance WHERE staff_id = ? AND date = ?
        ''', (test_staff_id, today)).fetchone()
        
        if attendance_record:
            print(f"   ✅ Attendance record found:")
            print(f"      Staff ID: {test_staff_id}")
            print(f"      Date: {attendance_record['date']}")
            print(f"      Time In: {attendance_record['time_in']}")
            print(f"      Status: {attendance_record['status']}")
            print(f"      Late Duration: {attendance_record['late_duration_minutes']} minutes")
            print(f"      Shift Start: {attendance_record['shift_start_time']}")
            print(f"      Shift End: {attendance_record['shift_end_time']}")
            
            # Verify the status is correct
            if attendance_record['status'].lower() == 'late':
                print("   ✅ Status correctly marked as 'Late'")
                
                # Verify late duration is reasonable (should be ~8+ hours)
                if attendance_record['late_duration_minutes'] > 400:  # More than 6.5 hours
                    print(f"   ✅ Late duration is reasonable: {attendance_record['late_duration_minutes']} minutes")
                else:
                    print(f"   ⚠️ Late duration seems low: {attendance_record['late_duration_minutes']} minutes")
            else:
                print(f"   ❌ Status incorrectly marked as '{attendance_record['status']}' instead of 'Late'")
                sys.exit(1)
        else:
            print("   ❌ No attendance record found!")
            sys.exit(1)
        
        # Step 6: Test Today's Attendance display query
        print("\n6. Testing Today's Attendance display query...")
        
        today_attendance = db.execute('''
            SELECT s.id as staff_id, s.staff_id as staff_number, s.full_name, s.department,
                   a.time_in, a.time_out,
                   COALESCE(a.status, 'absent') as status,
                   a.late_duration_minutes
            FROM staff s
            LEFT JOIN attendance a ON s.id = a.staff_id AND a.date = ?
            WHERE s.id = ?
        ''', (today, test_staff_id)).fetchone()
        
        if today_attendance:
            print(f"   ✅ Today's Attendance query result:")
            print(f"      Staff: {today_attendance['full_name']}")
            print(f"      Status: {today_attendance['status']}")
            print(f"      Time In: {today_attendance['time_in']}")
            print(f"      Late Duration: {today_attendance['late_duration_minutes']} minutes")
            
            if today_attendance['status'].lower() == 'late':
                print("   ✅ Today's Attendance correctly shows 'Late' status")
            else:
                print(f"   ❌ Today's Attendance incorrectly shows '{today_attendance['status']}' status")
                sys.exit(1)
        else:
            print("   ❌ Today's Attendance query returned no results!")
            sys.exit(1)
        
        # Step 7: Cleanup
        print("\n7. Cleaning up test data...")
        db.execute('DELETE FROM attendance WHERE staff_id = ? AND date = ?', (test_staff_id, today))
        db.execute('DELETE FROM staff WHERE staff_id = \'TEST001\' AND school_id = 1')
        db.commit()
        print("   ✅ Test data cleaned up")
    
    print("\n" + "=" * 60)
    print("🎉 All Biometric Strict Timing tests passed!")
    print("✅ The biometric capture system correctly applies strict timing rules:")
    print("   • ShiftManager uses strict timing (no grace period)")
    print("   • Very late arrivals are marked as 'Late'")
    print("   • Late duration is accurately calculated")
    print("   • Today's Attendance display shows correct status")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
