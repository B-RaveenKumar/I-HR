import sqlite3

db = sqlite3.connect('instance/vishnorex.db')
db.row_factory = sqlite3.Row
cursor = db.cursor()

print("Checking timetable_hierarchical_assignments for Velmurugan (ID=98):")
cursor.execute('SELECT * FROM timetable_hierarchical_assignments WHERE staff_id = 98 LIMIT 10')
assignments = cursor.fetchall()

if assignments:
    for a in assignments:
        day_names = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        day = day_names[a['day_of_week']] if a['day_of_week'] < 7 else 'Unknown'
        print(f"  ID: {a['id']}, {day}-P{a['period_number']}, Level: {a['level_id']}, Section: {a['section_id']}, Subject: {a['subject_name']}, Room: {a['room_number']}")
else:
    print("  None found")

print("\nAll recent hierarchical assignments:")
cursor.execute('SELECT ha.*, s.full_name FROM timetable_hierarchical_assignments ha JOIN staff s ON ha.staff_id = s.id ORDER BY ha.id DESC LIMIT 10')
recent = cursor.fetchall()
for a in recent:
    day_names = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    day = day_names[a['day_of_week']] if a['day_of_week'] < 7 else 'Unknown'
    print(f"  {a['full_name']} (ID:{a['staff_id']}): {day}-P{a['period_number']}, Level: {a['level_id']}, Section: {a['section_id']}")

db.close()
