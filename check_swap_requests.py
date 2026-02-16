import sqlite3

db = sqlite3.connect('instance/vishnorex.db')
db.row_factory = sqlite3.Row
cursor = db.cursor()

print("=== Recent Swap Requests ===")
cursor.execute('''
    SELECT tar.*, 
           s1.full_name as requester_name,
           s2.full_name as target_name
    FROM timetable_alteration_requests tar
    LEFT JOIN staff s1 ON tar.requester_staff_id = s1.id
    LEFT JOIN staff s2 ON tar.target_staff_id = s2.id
    ORDER BY tar.id DESC LIMIT 5
''')

requests = cursor.fetchall()
if requests:
    for r in requests:
        print(f"\nRequest ID: {r['id']}")
        print(f"  Requester: {r['requester_name']} (ID: {r['requester_staff_id']})")
        print(f"  Target: {r['target_name']} (ID: {r['target_staff_id']})")
        print(f"  Assignment ID: {r['assignment_id']}")
        print(f"  Status: {r['status']}")
        print(f"  Created: {r['created_at']}")
else:
    print("No swap requests found")

print("\n=== Checking if Assignment ID exists in hierarchical_assignments ===")
for r in requests:
    cursor.execute('SELECT * FROM timetable_hierarchical_assignments WHERE id = ?', (r['assignment_id'],))
    assignment = cursor.fetchone()
    if assignment:
        print(f"Assignment {r['assignment_id']}: EXISTS - Staff ID: {assignment['staff_id']}, Period: {assignment['period_number']}, Day: {assignment['day_of_week']}")
    else:
        print(f"Assignment {r['assignment_id']}: NOT FOUND in hierarchical_assignments")

print("\n=== Staff IDs ===")
cursor.execute("SELECT id, full_name FROM staff WHERE id IN (91, 98)")
for s in cursor.fetchall():
    print(f"  {s['full_name']}: ID = {s['id']}")

db.close()
