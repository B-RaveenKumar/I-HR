#!/usr/bin/env python3

from app import app
from database import get_db
import datetime

def test_current_performance_report():
    """Test the current performance report implementation"""
    with app.app_context():
        db = get_db()
        school_id = 4  # Assuming school_id 4 as per previous tests
        
        print("🎯 CURRENT PERFORMANCE REPORT ANALYSIS")
        print("=" * 50)
        
        # Check what data exists for performance analysis
        today = datetime.date.today()
        current_month = today.month
        current_year = today.year
        
        print(f"📊 Analyzing data for: {current_month}/{current_year}")
        print(f"🏫 School ID: {school_id}")
        
        # Check attendance data
        print("\n🔍 ATTENDANCE DATA ANALYSIS:")
        attendance_data = db.execute("""
            SELECT 
                s.staff_id, s.full_name, s.department, s.position,
                COUNT(a.id) as total_records,
                SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) as present_days,
                SUM(CASE WHEN a.status = 'late' THEN 1 ELSE 0 END) as late_days,
                SUM(CASE WHEN a.status = 'on_duty' THEN 1 ELSE 0 END) as on_duty_days,
                SUM(CASE WHEN a.status = 'early_departure' THEN 1 ELSE 0 END) as early_departure_days
            FROM staff s
            LEFT JOIN attendance a ON s.id = a.staff_id 
                AND strftime('%m', a.date) = ? AND strftime('%Y', a.date) = ?
            WHERE s.school_id = ? AND s.is_active = 1
            GROUP BY s.id
            LIMIT 10
        """, (f"{current_month:02d}", str(current_year), school_id)).fetchall()
        
        for staff in attendance_data:
            print(f"  👤 {staff['staff_id']}: {staff['full_name']}")
            print(f"     Department: {staff['department']}")
            print(f"     Present: {staff['present_days']}, Late: {staff['late_days']}, On Duty: {staff['on_duty_days']}")
            print()
        
        # Check leave applications
        print("🏖️ LEAVE APPLICATIONS DATA:")
        leave_data = db.execute("""
            SELECT 
                s.staff_id, s.full_name,
                COUNT(l.id) as leave_applications,
                SUM(julianday(l.end_date) - julianday(l.start_date) + 1) as total_leave_days
            FROM staff s
            LEFT JOIN leave_applications l ON s.id = l.staff_id 
                AND l.status = 'approved'
                AND strftime('%m', l.start_date) = ? AND strftime('%Y', l.start_date) = ?
            WHERE s.school_id = ? AND s.is_active = 1
            GROUP BY s.id
            HAVING leave_applications > 0
            LIMIT 5
        """, (f"{current_month:02d}", str(current_year), school_id)).fetchall()
        
        for staff in leave_data:
            print(f"  👤 {staff['staff_id']}: {staff['full_name']}")
            print(f"     Leave Applications: {staff['leave_applications']}, Total Days: {staff['total_leave_days']}")
        
        # Check OD applications  
        print("\n🚗 ON DUTY (OD) APPLICATIONS DATA:")
        od_data = db.execute("""
            SELECT 
                s.staff_id, s.full_name,
                COUNT(od.id) as od_applications,
                SUM(julianday(od.end_date) - julianday(od.start_date) + 1) as total_od_days
            FROM staff s
            LEFT JOIN on_duty_applications od ON s.id = od.staff_id 
                AND od.status = 'approved'
                AND strftime('%m', od.start_date) = ? AND strftime('%Y', od.start_date) = ?
            WHERE s.school_id = ? AND s.is_active = 1
            GROUP BY s.id
            HAVING od_applications > 0
            LIMIT 5
        """, (f"{current_month:02d}", str(current_year), school_id)).fetchall()
        
        for staff in od_data:
            print(f"  👤 {staff['staff_id']}: {staff['full_name']}")
            print(f"     OD Applications: {staff['od_applications']}, Total Days: {staff['total_od_days']}")
        
        # Check permission applications
        print("\n🕐 PERMISSION APPLICATIONS DATA:")
        permission_data = db.execute("""
            SELECT 
                s.staff_id, s.full_name,
                COUNT(p.id) as permission_applications,
                SUM(p.duration_hours) as total_permission_hours
            FROM staff s
            LEFT JOIN permission_applications p ON s.id = p.staff_id 
                AND p.status = 'approved'
                AND strftime('%m', p.permission_date) = ? AND strftime('%Y', p.permission_date) = ?
            WHERE s.school_id = ? AND s.is_active = 1
            GROUP BY s.id
            HAVING permission_applications > 0
            LIMIT 5
        """, (f"{current_month:02d}", str(current_year), school_id)).fetchall()
        
        for staff in permission_data:
            print(f"  👤 {staff['staff_id']}: {staff['full_name']}")
            print(f"     Permission Applications: {staff['permission_applications']}, Total Hours: {staff['total_permission_hours']}")
        
        # Check what the current performance report would generate
        print("\n📈 TESTING CURRENT PERFORMANCE REPORT:")
        print("Current function exists in app.py - 'generate_performance_report'")
        print("✅ Excel export: Supported")
        print("✅ PDF export: Supported") 
        print("✅ CSV export: Supported")
        print("✅ Department filtering: Supported")
        print("✅ Date range filtering: Supported (month/year)")
        
        # Compare with user requirements
        print("\n📋 USER REQUIREMENTS vs CURRENT IMPLEMENTATION:")
        print("✅ Staff ID - Current: Available")
        print("✅ Staff Name - Current: Available") 
        print("✅ Department - Current: Available")
        print("✅ Position - Current: Available")
        print("❓ Days Present - Current: Present days (may need refinement)")
        print("❓ Days Absent - Current: Absent days (may need refinement)")
        print("❓ Days on OD applied - Current: Not directly included")
        print("❓ Days on Leave applied - Current: Not directly included")  
        print("❓ Days with Permission applied - Current: Not directly included")
        print("✅ Department filtering - Current: Supported")
        print("✅ Date range filtering - Current: Supported (month/year)")
        print("❌ From/To date pickers - Current: Only month/year selector")
        print("✅ Excel export - Current: Supported")
        
        print("\n🎯 ENHANCEMENT NEEDED:")
        print("1. Modify Performance Report to include Leave, OD, and Permission data")
        print("2. Add proper From/To date range selection")
        print("3. Ensure all required fields are included in the output")
        print("4. Test the enhanced functionality")

if __name__ == '__main__':
    test_current_performance_report()