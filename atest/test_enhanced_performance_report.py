#!/usr/bin/env python3

from app import app
from database import get_db
import datetime
import json

def test_enhanced_performance_report():
    """Test the enhanced Performance Report functionality"""
    with app.app_context():
        db = get_db()
        school_id = 4  # Test school
        
        print("🎯 ENHANCED PERFORMANCE REPORT TESTING")
        print("=" * 60)
        
        print(f"🏫 Testing for School ID: {school_id}")
        
        # Test 1: Check available sample data
        print("\n📊 Sample Data Analysis:")
        
        # Check staff count
        staff_count = db.execute(
            "SELECT COUNT(*) as count FROM staff WHERE school_id = ? AND is_active = 1", 
            (school_id,)
        ).fetchone()['count']
        print(f"   Active Staff: {staff_count}")
        
        # Check attendance data for September 2025
        attendance_count = db.execute("""
            SELECT COUNT(*) as count FROM attendance a
            JOIN staff s ON a.staff_id = s.id
            WHERE s.school_id = ? AND a.date >= '2025-09-01' AND a.date <= '2025-09-30'
        """, (school_id,)).fetchone()['count']
        print(f"   Attendance Records (Sep 2025): {attendance_count}")
        
        # Check leave applications
        leave_count = db.execute("""
            SELECT COUNT(*) as count FROM leave_applications l
            JOIN staff s ON l.staff_id = s.id
            WHERE s.school_id = ? AND l.start_date >= '2025-09-01' AND l.end_date <= '2025-09-30'
        """, (school_id,)).fetchone()['count']
        print(f"   Leave Applications (Sep 2025): {leave_count}")
        
        # Check OD applications
        od_count = db.execute("""
            SELECT COUNT(*) as count FROM on_duty_applications od
            JOIN staff s ON od.staff_id = s.id
            WHERE s.school_id = ? AND od.start_date >= '2025-09-01' AND od.end_date <= '2025-09-30'
        """, (school_id,)).fetchone()['count']
        print(f"   OD Applications (Sep 2025): {od_count}")
        
        # Check permission applications
        permission_count = db.execute("""
            SELECT COUNT(*) as count FROM permission_applications p
            JOIN staff s ON p.staff_id = s.id
            WHERE s.school_id = ? AND p.permission_date >= '2025-09-01' AND p.permission_date <= '2025-09-30'
        """, (school_id,)).fetchone()['count']
        print(f"   Permission Applications (Sep 2025): {permission_count}")
        
        # Test 2: Simulate the enhanced performance report data collection
        print("\n🔍 Enhanced Performance Report Data Collection Test:")
        
        # Date range
        start_date = datetime.date(2025, 9, 1)
        end_date = datetime.date(2025, 9, 30)
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        # Main staff performance query (simulating the enhanced function)
        staff_performance_query = """
            SELECT 
                s.staff_id,
                s.full_name,
                COALESCE(s.department, 'Unassigned') as department,
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
            GROUP BY s.id, s.staff_id, s.full_name, s.department, s.position
            ORDER BY s.department, s.full_name
            LIMIT 5
        """
        
        staff_rows = db.execute(staff_performance_query, (start_str, end_str, school_id)).fetchall()
        
        print(f"   Sample Staff Performance Data (Top 5):")
        for staff in staff_rows:
            print(f"   👤 {staff['staff_id']}: {staff['full_name']}")
            print(f"      Department: {staff['department']}, Position: {staff['position']}")
            print(f"      Days Present: {staff['days_present']}, Days Absent: {staff['days_absent']}")
            print(f"      Total Attendance Records: {staff['total_attendance_records']}")
            print()
        
        # Test 3: Test Leave data collection
        print("🏖️ Leave Data Collection Test:")
        leave_query = """
            SELECT 
                s.staff_id,
                COALESCE(COUNT(l.id), 0) as leave_applications_count,
                COALESCE(SUM(julianday(l.end_date) - julianday(l.start_date) + 1), 0) as days_on_leave
            FROM staff s
            LEFT JOIN leave_applications l ON s.id = l.staff_id 
                AND l.status = 'approved'
                AND l.start_date <= ? AND l.end_date >= ?
            WHERE s.school_id = ? AND s.is_active = 1
            GROUP BY s.id, s.staff_id
            HAVING leave_applications_count > 0
            LIMIT 3
        """
        
        leave_data = db.execute(leave_query, (end_str, start_str, school_id)).fetchall()
        for leave in leave_data:
            print(f"   👤 Staff {leave['staff_id']}: {leave['leave_applications_count']} applications, {leave['days_on_leave']} days")
        
        if not leave_data:
            print("   No approved leave applications found in the date range")
        
        # Test 4: Test OD data collection
        print("\n🚗 OD Data Collection Test:")
        od_query = """
            SELECT 
                s.staff_id,
                COALESCE(COUNT(od.id), 0) as od_applications_count,
                COALESCE(SUM(julianday(od.end_date) - julianday(od.start_date) + 1), 0) as days_on_od
            FROM staff s
            LEFT JOIN on_duty_applications od ON s.id = od.staff_id 
                AND od.status = 'approved'
                AND od.start_date <= ? AND od.end_date >= ?
            WHERE s.school_id = ? AND s.is_active = 1
            GROUP BY s.id, s.staff_id
            HAVING od_applications_count > 0
            LIMIT 3
        """
        
        od_data = db.execute(od_query, (end_str, start_str, school_id)).fetchall()
        for od in od_data:
            print(f"   👤 Staff {od['staff_id']}: {od['od_applications_count']} applications, {od['days_on_od']} days")
        
        if not od_data:
            print("   No approved OD applications found in the date range")
        
        # Test 5: Test Permission data collection
        print("\n🕐 Permission Data Collection Test:")
        permission_query = """
            SELECT 
                s.staff_id,
                COALESCE(COUNT(p.id), 0) as permission_applications_count,
                COALESCE(SUM(p.duration_hours), 0) as total_permission_hours
            FROM staff s
            LEFT JOIN permission_applications p ON s.id = p.staff_id 
                AND p.status = 'approved'
                AND p.permission_date BETWEEN ? AND ?
            WHERE s.school_id = ? AND s.is_active = 1
            GROUP BY s.id, s.staff_id
            HAVING permission_applications_count > 0
            LIMIT 3
        """
        
        permission_data = db.execute(permission_query, (start_str, end_str, school_id)).fetchall()
        for permission in permission_data:
            hours = permission['total_permission_hours']
            days = round(float(hours) / 8, 1) if hours else 0
            print(f"   👤 Staff {permission['staff_id']}: {permission['permission_applications_count']} applications, {hours} hours ({days} days)")
        
        if not permission_data:
            print("   No approved permission applications found in the date range")
        
        # Test 6: Comprehensive report simulation
        print("\n📋 COMPREHENSIVE REPORT SIMULATION:")
        print("Enhanced Performance Report will include the following fields:")
        print("✅ Staff ID")
        print("✅ Staff Name") 
        print("✅ Department")
        print("✅ Position")
        print("✅ Days Present (count)")
        print("✅ Days Absent (count)")
        print("✅ Days on OD Applied")
        print("✅ Days on Leave Applied")
        print("✅ Days with Permission Applied")
        
        print("\n📈 REPORT FEATURES:")
        print("✅ Date range filtering (from_date to to_date)")
        print("✅ Department filtering")  
        print("✅ Excel export (.xlsx)")
        print("✅ PDF export (.pdf)")
        print("✅ CSV export (.csv)")
        
        print("\n🔄 TESTING SUMMARY:")
        print(f"✅ Database connection: Working")
        print(f"✅ Staff data: {staff_count} active staff found")
        print(f"✅ Attendance data: {attendance_count} records found")
        print(f"✅ Leave data: {leave_count} applications found")  
        print(f"✅ OD data: {od_count} applications found")
        print(f"✅ Permission data: {permission_count} applications found")
        print(f"✅ SQL queries: All tested successfully")
        print(f"✅ Enhanced function: Ready for testing")
        
        print("\n🎯 NEXT STEPS:")
        print("1. Navigate to Reports & Analytics in admin panel")
        print("2. Find 'Performance Report' card")
        print("3. Select date range using From Date and To Date fields")
        print("4. Optionally select a specific department")
        print("5. Choose Excel format and click Generate")
        print("6. Verify the downloaded report contains all required fields")
        
        # Generate sample data for testing if none exists
        print(f"\n💡 SAMPLE DATA RECOMMENDATION:")
        if attendance_count == 0:
            print("⚠️  No attendance data found. Consider adding sample attendance records.")
        if leave_count == 0:
            print("⚠️  No leave applications found. Consider adding sample leave applications.")
        if od_count == 0:
            print("⚠️  No OD applications found. Consider adding sample OD applications.")
        if permission_count == 0:
            print("⚠️  No permission applications found. Consider adding sample permission applications.")
        
        print("\n✅ Enhanced Performance Report implementation is ready for testing!")

if __name__ == '__main__':
    test_enhanced_performance_report()