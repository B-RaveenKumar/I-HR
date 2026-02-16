#!/usr/bin/env python
"""Check staff assignments for debugging"""
import sqlite3

db = sqlite3.connect('instance/vishnorex.db')
db.row_factory = sqlite3.Row
cursor = db.cursor()

print("=" * 60)
print("STAFF RECORDS - Velmurugan")
print("=" * 60)
cursor.execute('''
    SELECT id, full_name, department, school_id 
    FROM staff 
    WHERE full_name LIKE "%Velmurugan%" 
    LIMIT 5
''')
staff_records = cursor.fetchall()
for r in staff_records:
    print(f"  ID: {r['id']}, Name: {r['full_name']}, Dept: {r['department']}, School: {r['school_id']}")

if staff_records:
    staff_ids = [r['id'] for r in staff_records]
    print(f"\nStaff IDs: {staff_ids}")
    
    print("\n" + "=" * 60)
    print("TIMETABLE ASSIGNMENTS")
    print("=" * 60)
    placeholders = ','.join('?' * len(staff_ids))
    cursor.execute(f'''
        SELECT ta.id, ta.staff_id, ta.day_of_week, ta.period_number, 
               ta.class_subject, ta.school_id, ta.is_locked,
               tp.period_name, tp.start_time, tp.end_time
        FROM timetable_assignments ta
        LEFT JOIN timetable_periods tp ON ta.school_id = tp.school_id 
                                       AND ta.period_number = tp.period_number
        WHERE ta.staff_id IN ({placeholders})
        ORDER BY ta.day_of_week, ta.period_number
    ''', staff_ids)
    
    assignments = cursor.fetchall()
    if assignments:
        for a in assignments:
            day_names = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
            day = day_names[a['day_of_week']] if a['day_of_week'] < 7 else 'Unknown'
            print(f"  Assignment ID: {a['id']}")
            print(f"    Staff ID: {a['staff_id']}, School: {a['school_id']}")
            print(f"    Day: {day} ({a['day_of_week']}), Period: {a['period_number']}")
            print(f"    Subject: {a['class_subject']}")
            print(f"    Time: {a['start_time']} - {a['end_time']}")
            print(f"    Locked: {bool(a['is_locked'])}")
            print()
    else:
        print("  No assignments found!")
else:
    print("  No staff records found!")

print("=" * 60)
print("ALL RECENT TIMETABLE ASSIGNMENTS (Last 10)")
print("=" * 60)
cursor.execute('''
    SELECT ta.id, ta.staff_id, s.full_name, ta.day_of_week, ta.period_number, 
           ta.class_subject, ta.school_id
    FROM timetable_assignments ta
    JOIN staff s ON ta.staff_id = s.id
    ORDER BY ta.id DESC
    LIMIT 10
''')
for a in cursor.fetchall():
    day_names = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    day = day_names[a['day_of_week']] if a['day_of_week'] < 7 else 'Unknown'
    print(f"  ID: {a['id']}, Staff: {a['full_name']} (ID:{a['staff_id']}), {day}-P{a['period_number']}, Subject: {a['class_subject']}")

db.close()
