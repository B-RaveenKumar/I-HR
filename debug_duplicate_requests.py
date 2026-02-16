import sqlite3

db = sqlite3.connect('instance/vishnorex.db')
db.row_factory = sqlite3.Row
cursor = db.cursor()

staff_id = 98  # Velmurugan P
school_id = 4

print("=== Testing current query ===")
cursor.execute('''
    SELECT tar.id, tar.requester_staff_id, s.full_name as requester_name, s.department as requester_dept,
           tar.assignment_id, tar.reason, tar.status, tar.created_at,
           tp.period_name, tp.start_time, tp.end_time, ha.period_number, ha.day_of_week,
           ha.subject_name, l.level_name, sec.section_name
    FROM timetable_alteration_requests tar
    JOIN staff s ON tar.requester_staff_id = s.id
    JOIN timetable_hierarchical_assignments ha ON tar.assignment_id = ha.id
    LEFT JOIN timetable_periods tp ON ha.school_id = tp.school_id 
        AND ha.period_number = tp.period_number
        AND ha.level_id = tp.level_id
        AND ha.section_id = tp.section_id
    LEFT JOIN timetable_academic_levels l ON ha.level_id = l.id
    LEFT JOIN timetable_sections sec ON ha.section_id = sec.id
    WHERE tar.target_staff_id = ? AND tar.school_id = ? AND tar.status = 'pending'
    ORDER BY tar.created_at DESC
''', (staff_id, school_id))

requests = cursor.fetchall()
print(f"Query returned {len(requests)} rows:")
for r in requests:
    print(f"  Request ID: {r['id']}, Assignment: {r['assignment_id']}, From: {r['requester_name']}, Level: {r['level_name']}, Section: {r['section_name']}")

print("\n=== Unique request IDs ===")
unique_ids = set()
for r in requests:
    unique_ids.add(r['id'])
print(f"Unique requests: {len(unique_ids)} - IDs: {sorted(unique_ids)}")

print("\n=== Check assignment 18 details ===")
cursor.execute('SELECT * FROM timetable_hierarchical_assignments WHERE id = 18')
assignment = cursor.fetchone()
if assignment:
    print(f"Assignment 18: level_id={assignment['level_id']}, section_id={assignment['section_id']}, period={assignment['period_number']}")
    
print("\n=== Check if multiple level/section records exist ===")
cursor.execute('SELECT * FROM timetable_academic_levels WHERE id = ?', (assignment['level_id'],))
levels = cursor.fetchall()
print(f"Levels for ID {assignment['level_id']}: {len(levels)}")
for l in levels:
    print(f"  Level: {l['level_name']}, school_id={l['school_id']}")

cursor.execute('SELECT * FROM timetable_sections WHERE id = ?', (assignment['section_id'],))
sections = cursor.fetchall()
print(f"Sections for ID {assignment['section_id']}: {len(sections)}")
for sec in sections:
    print(f"  Section: {sec['section_name']}, school_id={sec['school_id']}")

print("\n=== Check period records ===")
cursor.execute('SELECT * FROM timetable_periods WHERE school_id = ? AND period_number = ?', (assignment['school_id'], assignment['period_number']))
periods = cursor.fetchall()
print(f"Period records for school {assignment['school_id']}, period {assignment['period_number']}: {len(periods)}")
for p in periods:
    print(f"  Period: {p['period_name']}, {p['start_time']}-{p['end_time']}, id={p['id']}")

db.close()
