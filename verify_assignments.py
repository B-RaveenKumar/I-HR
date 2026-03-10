"""
Verify current assignments in database after cleanup
"""

import sqlite3
import os

def main():
    db_path = os.path.join('instance', 'vishnorex.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("CURRENT DATABASE STATE - ALL ASSIGNMENT TABLES")
    print("="*80)
    
    day_names = {1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 
                4: 'Thursday', 5: 'Friday', 6: 'Saturday'}
    
    # Check timetable_assignments
    print("\n1. timetable_assignments (OLD DIRECT ASSIGNMENTS):")
    print("-" * 80)
    cursor.execute("""
        SELECT staff_id, day_of_week, period_number, class_subject
        FROM timetable_assignments
        WHERE staff_id IS NOT NULL
        ORDER BY staff_id, day_of_week, period_number
    """)
    old_assignments = cursor.fetchall()
    if old_assignments:
        for a in old_assignments:
            day = day_names.get(a['day_of_week'], f"Day {a['day_of_week']}")
            print(f"  Staff {a['staff_id']}: {day}, Period {a['period_number']} - {a['class_subject']}")
    else:
        print("  ✓ No old assignments (cleaned up successfully)")
    
    # Check timetable_hierarchical_assignments
    print("\n2. timetable_hierarchical_assignments (NEW HIERARCHICAL SYSTEM):")
    print("-" * 80)
    cursor.execute("""
        SELECT staff_id, day_of_week, period_number, subject_name, section_id
        FROM timetable_hierarchical_assignments
        WHERE staff_id IS NOT NULL
        ORDER BY staff_id, day_of_week, period_number
    """)
    hierarchical = cursor.fetchall()
    if hierarchical:
        for a in hierarchical:
            day = day_names.get(a['day_of_week'], f"Day {a['day_of_week']}")
            print(f"  Staff {a['staff_id']}: {day}, Period {a['period_number']} - {a['subject_name']} (Section {a['section_id']})")
    else:
        print("  (No hierarchical assignments)")
    
    # Check timetable_self_allocations
    print("\n3. timetable_self_allocations (SELF-ALLOCATED PERIODS):")
    print("-" * 80)
    cursor.execute("""
        SELECT staff_id, day_of_week, period_number, class_subject
        FROM timetable_self_allocations
        WHERE staff_id IS NOT NULL
        ORDER BY staff_id, day_of_week, period_number
    """)
    self_alloc = cursor.fetchall()
    if self_alloc:
        for a in self_alloc:
            day = day_names.get(a['day_of_week'], f"Day {a['day_of_week']}")
            print(f"  Staff {a['staff_id']}: {day}, Period {a['period_number']} - {a['class_subject']}")
    else:
        print("  (No self-allocated periods)")
    
    # Summary for Staff ID 91 (Manjukumaran C)
    print("\n" + "="*80)
    print("SUMMARY FOR STAFF ID 91 (Manjukumaran C) - MONDAY:")
    print("="*80)
    
    all_periods = []
    
    # From old assignments
    cursor.execute("""
        SELECT period_number, 'timetable_assignments' as source
        FROM timetable_assignments
        WHERE staff_id = 91 AND day_of_week = 1
    """)
    for row in cursor.fetchall():
        all_periods.append((row['period_number'], row['source']))
    
    # From hierarchical
    cursor.execute("""
        SELECT period_number, 'timetable_hierarchical_assignments' as source
        FROM timetable_hierarchical_assignments
        WHERE staff_id = 91 AND day_of_week = 1
    """)
    for row in cursor.fetchall():
        all_periods.append((row['period_number'], row['source']))
    
    # From self allocations
    cursor.execute("""
        SELECT period_number, 'timetable_self_allocations' as source
        FROM timetable_self_allocations
        WHERE staff_id = 91 AND day_of_week = 1
    """)
    for row in cursor.fetchall():
        all_periods.append((row['period_number'], row['source']))
    
    if all_periods:
        print(f"Total assigned periods: {len(all_periods)}")
        for period, source in sorted(all_periods):
            print(f"  Period {period} - from {source}")
    else:
        print("  No assignments found for staff 91 on Monday")
    
    print("\n" + "="*80)
    print("NEXT STEP: Restart Flask application to see changes")
    print("="*80 + "\n")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
