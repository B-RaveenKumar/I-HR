#!/usr/bin/env python
"""Test database connectivity for timetable management"""

from database import get_db

def test_database():
    try:
        db = get_db()
        
        # Check periods
        print("=" * 60)
        print("CHECKING PERIODS TABLE")
        print("=" * 60)
        periods = db.execute('SELECT * FROM timetable_periods LIMIT 10').fetchall()
        print(f"Total periods found: {len(periods)}")
        for p in periods:
            print(f"  Period {p['period_number']}: {p['period_name']} ({p['start_time']} - {p['end_time']})")
        
        # Check staff
        print("\n" + "=" * 60)
        print("CHECKING STAFF TABLE")
        print("=" * 60)
        staff = db.execute('SELECT * FROM staff WHERE school_id=1 LIMIT 10').fetchall()
        print(f"Total staff found for school_id=1: {len(staff)}")
        for s in staff:
            print(f"  {s['staff_id']}: {s['full_name']} ({s['department']})")
        
        # Check departments
        print("\n" + "=" * 60)
        print("CHECKING DEPARTMENTS TABLE")
        print("=" * 60)
        depts = db.execute('SELECT DISTINCT department FROM staff WHERE school_id=1').fetchall()
        print(f"Total unique departments: {len(depts)}")
        for d in depts:
            print(f"  {d['department']}")
        
        # Check schools
        print("\n" + "=" * 60)
        print("CHECKING SCHOOLS TABLE")
        print("=" * 60)
        schools = db.execute('SELECT * FROM school LIMIT 5').fetchall()
        print(f"Total schools: {len(schools)}")
        for s in schools:
            print(f"  School {s['id']}: {s.get('school_name', 'Unknown')}")
        
        print("\n" + "=" * 60)
        print("DATABASE CONNECTION: OK ✓")
        print("=" * 60)
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_database()
