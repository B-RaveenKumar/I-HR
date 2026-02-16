import sqlite3

db = sqlite3.connect('instance/vishnorex.db')
db.row_factory = sqlite3.Row
cursor = db.cursor()

staff_id = 98  # Velmurugan P
school_id = 4

print(f"Testing query for staff_id={staff_id}, school_id={school_id}\n")

# Test the exact query from the endpoint
cursor.execute('''
    SELECT tar.id, tar.requester_staff_id, s.full_name as requester_name, s.department as requester_dept,
           tar.assignment_id, tar.reason, tar.status, tar.created_at,
           tp.period_name, tp.start_time, tp.end_time, ha.period_number, ha.day_of_week,
           ha.subject_name, l.level_name, sec.section_name
    FROM timetable_alteration_requests tar
    JOIN staff s ON tar.requester_staff_id = s.id
    JOIN timetable_hierarchical_assignments ha ON tar.assignment_id = ha.id
    LEFT JOIN timetable_periods tp ON ha.school_id = tp.school_id AND ha.period_number = tp.period_number
    LEFT JOIN timetable_academic_levels l ON ha.level_id = l.id
    LEFT JOIN timetable_sections sec ON ha.section_id = sec.id
    WHERE tar.target_staff_id = ? AND tar.school_id = ? AND tar.status = 'pending'
    ORDER BY tar.created_at DESC
''', (staff_id, school_id))

requests = cursor.fetchall()
print(f"Found {len(requests)} requests\n")

if requests:
    for r in requests:
        print(f"Request ID: {r['id']}")
        print(f"  From: {r['requester_name']} ({r['requester_dept']})")
        print(f"  Assignment ID: {r['assignment_id']}")
        print(f"  Period: P{r['period_number']} on Day {r['day_of_week']}")
        print(f"  Subject: {r['subject_name']}")
        print(f"  Level: {r['level_name']}, Section: {r['section_name']}")
        print()
else:
    print("No requests returned by query")
    
    # Debug: Check what requests exist at all
    print("\n=== All pending requests for this target ===")
    cursor.execute('''
        SELECT * FROM timetable_alteration_requests 
        WHERE target_staff_id = ? AND status = 'pending'
    ''', (staff_id,))
    all_requests = cursor.fetchall()
    print(f"Found {len(all_requests)} total pending requests")
    for r in all_requests:
        print(f"  Request {r['id']}: school_id={r['school_id']}, assignment_id={r['assignment_id']}")

db.close()
