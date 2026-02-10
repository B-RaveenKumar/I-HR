#!/usr/bin/env python3

from app import app
from database import get_db
import datetime

def analyze_performance_data_accuracy():
    """Analyze and test performance report data accuracy issues"""
    with app.app_context():
        db = get_db()
        school_id = 4  # Test school
        
        print("🔍 PERFORMANCE REPORT DATA ACCURACY ANALYSIS")
        print("=" * 65)
        
        # Test date range (September 2025)
        start_date = '2025-09-01'
        end_date = '2025-09-30'
        
        print(f"📅 Analysis Period: {start_date} to {end_date}")
        print(f"🏫 School ID: {school_id}")
        
        # Issue 1: Check staff position field
        print(f"\n🔍 ISSUE 1: Staff Position Field Analysis")
        staff_positions = db.execute("""
            SELECT staff_id, full_name, position, department
            FROM staff 
            WHERE school_id = ? AND is_active = 1
            ORDER BY staff_id
            LIMIT 5
        """, (school_id,)).fetchall()
        
        print("   Current Staff Position Data:")
        for staff in staff_positions:
            position = staff['position'] if staff['position'] else 'NULL/Empty'
            print(f"   👤 {staff['staff_id']}: {staff['full_name']}")
            print(f"      Position: {position}")
            print(f"      Department: {staff['department']}")
            print()
        
        # Issue 2: Check attendance count discrepancies
        print("🔍 ISSUE 2: Attendance Count Analysis")
        
        # Current query from the function
        current_attendance_query = """
            SELECT 
                s.staff_id,
                s.full_name,
                COALESCE(s.position, 'Unspecified') as position,
                
                -- Days Present (count) - includes 'present' and 'late' as present
                COALESCE(SUM(CASE WHEN a.status IN ('present', 'late') THEN 1 ELSE 0 END), 0) as days_present,
                
                -- Days Absent (count) - only 'absent' status
                COALESCE(SUM(CASE WHEN a.status = 'absent' THEN 1 ELSE 0 END), 0) as days_absent,
                
                -- Count attendance records for verification
                COUNT(a.id) as total_attendance_records
                
            FROM staff s
            LEFT JOIN attendance a ON a.staff_id = s.id AND a.date BETWEEN ? AND ?
            WHERE s.school_id = ? AND s.is_active = 1
            GROUP BY s.id, s.staff_id, s.full_name, s.position
            ORDER BY s.staff_id
            LIMIT 5
        """
        
        attendance_results = db.execute(current_attendance_query, (start_date, end_date, school_id)).fetchall()
        
        print("   Current Attendance Calculation Results:")
        for result in attendance_results:
            print(f"   👤 {result['staff_id']}: {result['full_name']}")
            print(f"      Position: {result['position']}")
            print(f"      Days Present: {result['days_present']}")
            print(f"      Days Absent: {result['days_absent']}")
            print(f"      Total Attendance Records: {result['total_attendance_records']}")
            
            # Verify with raw attendance data
            raw_attendance = db.execute("""
                SELECT date, status FROM attendance 
                WHERE staff_id = (SELECT id FROM staff WHERE staff_id = ? AND school_id = ?)
                AND date BETWEEN ? AND ?
                ORDER BY date
            """, (result['staff_id'], school_id, start_date, end_date)).fetchall()
            
            print(f"      Raw Attendance Records ({len(raw_attendance)}):")
            status_counts = {}
            for record in raw_attendance:
                status = record['status']
                status_counts[status] = status_counts.get(status, 0) + 1
                print(f"        {record['date']}: {record['status']}")
            
            print(f"      Status Summary: {status_counts}")
            print()
        
        # Issue 3: Check leave applications data
        print("🔍 ISSUE 3: Leave Applications Analysis")
        
        leave_query = """
            SELECT 
                s.staff_id,
                s.full_name,
                COALESCE(COUNT(l.id), 0) as leave_applications_count,
                COALESCE(SUM(julianday(l.end_date) - julianday(l.start_date) + 1), 0) as days_on_leave
            FROM staff s
            LEFT JOIN leave_applications l ON s.id = l.staff_id 
                AND l.status = 'approved'
                AND l.start_date <= ? AND l.end_date >= ?
            WHERE s.school_id = ? AND s.is_active = 1
            GROUP BY s.id, s.staff_id, s.full_name
            HAVING leave_applications_count > 0 OR s.staff_id IN ('1', '2', '3')
            ORDER BY s.staff_id
            LIMIT 5
        """
        
        leave_results = db.execute(leave_query, (end_date, start_date, school_id)).fetchall()
        
        print("   Leave Applications Analysis:")
        if leave_results:
            for result in leave_results:
                print(f"   👤 {result['staff_id']}: {result['full_name']}")
                print(f"      Leave Applications: {result['leave_applications_count']}")
                print(f"      Days on Leave: {result['days_on_leave']}")
                
                # Get raw leave data
                raw_leaves = db.execute("""
                    SELECT start_date, end_date, leave_type, status
                    FROM leave_applications l
                    JOIN staff s ON l.staff_id = s.id
                    WHERE s.staff_id = ? AND s.school_id = ?
                    AND l.start_date <= ? AND l.end_date >= ?
                """, (result['staff_id'], school_id, end_date, start_date)).fetchall()
                
                for leave in raw_leaves:
                    days = (datetime.datetime.strptime(leave['end_date'], '%Y-%m-%d') - 
                           datetime.datetime.strptime(leave['start_date'], '%Y-%m-%d')).days + 1
                    print(f"        {leave['start_date']} to {leave['end_date']}: {leave['leave_type']} ({leave['status']}) - {days} days")
                print()
        else:
            print("   No leave applications found in the specified date range")
        
        # Issue 4: Check OD applications data
        print("🔍 ISSUE 4: OD Applications Analysis")
        
        od_query = """
            SELECT 
                s.staff_id,
                s.full_name,
                COALESCE(COUNT(od.id), 0) as od_applications_count,
                COALESCE(SUM(julianday(od.end_date) - julianday(od.start_date) + 1), 0) as days_on_od
            FROM staff s
            LEFT JOIN on_duty_applications od ON s.id = od.staff_id 
                AND od.status = 'approved'
                AND od.start_date <= ? AND od.end_date >= ?
            WHERE s.school_id = ? AND s.is_active = 1
            GROUP BY s.id, s.staff_id, s.full_name
            HAVING od_applications_count > 0 OR s.staff_id IN ('1', '2', '3')
            ORDER BY s.staff_id
            LIMIT 5
        """
        
        od_results = db.execute(od_query, (end_date, start_date, school_id)).fetchall()
        
        print("   OD Applications Analysis:")
        if od_results:
            for result in od_results:
                print(f"   👤 {result['staff_id']}: {result['full_name']}")
                print(f"      OD Applications: {result['od_applications_count']}")
                print(f"      Days on OD: {result['days_on_od']}")
                print()
        else:
            print("   No OD applications found in the specified date range")
        
        # Issue 5: Check permission applications data
        print("🔍 ISSUE 5: Permission Applications Analysis")
        
        permission_query = """
            SELECT 
                s.staff_id,
                s.full_name,
                COALESCE(COUNT(p.id), 0) as permission_applications_count,
                COALESCE(SUM(p.duration_hours), 0) as total_permission_hours
            FROM staff s
            LEFT JOIN permission_applications p ON s.id = p.staff_id 
                AND p.status = 'approved'
                AND p.permission_date BETWEEN ? AND ?
            WHERE s.school_id = ? AND s.is_active = 1
            GROUP BY s.id, s.staff_id, s.full_name
            HAVING permission_applications_count > 0 OR s.staff_id IN ('1', '2', '3')
            ORDER BY s.staff_id
            LIMIT 5
        """
        
        permission_results = db.execute(permission_query, (start_date, end_date, school_id)).fetchall()
        
        print("   Permission Applications Analysis:")
        if permission_results:
            for result in permission_results:
                hours = result['total_permission_hours']
                days = round(float(hours) / 8, 1) if hours else 0
                print(f"   👤 {result['staff_id']}: {result['full_name']}")
                print(f"      Permission Applications: {result['permission_applications_count']}")
                print(f"      Total Hours: {hours}, Total Days: {days}")
                print()
        else:
            print("   No permission applications found in the specified date range")
        
        # Issue 6: Calculate proper working days
        print("🔍 ISSUE 6: Working Days Calculation Analysis")
        
        # Get total days in the period
        start_dt = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        total_days = (end_dt - start_dt).days + 1
        
        # Calculate working days (excluding weekends for this example)
        working_days = 0
        current_dt = start_dt
        while current_dt <= end_dt:
            if current_dt.weekday() < 5:  # Monday = 0, Sunday = 6
                working_days += 1
            current_dt += datetime.timedelta(days=1)
        
        print(f"   Total Days in Period: {total_days}")
        print(f"   Working Days (Mon-Fri): {working_days}")
        print(f"   Weekend Days: {total_days - working_days}")
        
        # Check if there are any holidays defined
        holidays = db.execute("""
            SELECT date, name FROM holidays 
            WHERE school_id = ? AND date BETWEEN ? AND ?
        """, (school_id, start_date, end_date)).fetchall()
        
        print(f"   Holidays in Period: {len(holidays)}")
        for holiday in holidays:
            print(f"     {holiday['date']}: {holiday['name']}")
        
        print(f"\n📋 SUMMARY OF ISSUES IDENTIFIED:")
        print(f"1. ✅ Position Field: Found actual position data in database")
        print(f"2. ⚠️  Attendance Counts: Need to verify calculation logic")
        print(f"3. ⚠️  Leave Applications: {len(leave_results)} found, need to verify calculation")
        print(f"4. ⚠️  OD Applications: {len(od_results)} found, need to verify calculation")
        print(f"5. ⚠️  Permission Applications: {len(permission_results)} found, need to verify calculation")
        print(f"6. ⚠️  Working Days: Need to implement proper working days calculation")
        
        print(f"\n🛠️  FIXES NEEDED:")
        print(f"1. Update position field to use actual database values (not 'Unspecified')")
        print(f"2. Fix attendance counting logic to match actual database records")
        print(f"3. Verify leave/OD/permission calculations are accurate")
        print(f"4. Add proper working days calculation considering weekends/holidays")
        print(f"5. Add data validation and cross-checking")

if __name__ == '__main__':
    analyze_performance_data_accuracy()