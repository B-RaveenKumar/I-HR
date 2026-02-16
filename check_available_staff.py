import sqlite3

db = sqlite3.connect('instance/vishnorex.db')
db.row_factory = sqlite3.Row
cursor = db.cursor()

school_id = 4
department = "Development"
current_user_id = 98  # Velmurugan P
day_of_week = 1  # Monday
period_number = 1  # Period 1

print("=== All staff in Development department ===")
cursor.execute('SELECT id, full_name, department FROM staff WHERE school_id = ? AND department = ?', 
               (school_id, department))
all_dev_staff = cursor.fetchall()
for s in all_dev_staff:
    print(f"  {s['full_name']} (ID: {s['id']})")

print(f"\n=== Staff with assignments on Monday Period 1 ===")
cursor.execute('''
    SELECT ha.staff_id, s.full_name 
    FROM timetable_hierarchical_assignments ha
    JOIN staff s ON ha.staff_id = s.id
    WHERE ha.school_id = ? AND ha.day_of_week = ? AND ha.period_number = ?
''', (school_id, day_of_week, period_number))
busy_staff = cursor.fetchall()
for s in busy_staff:
    print(f"  {s['full_name']} (ID: {s['staff_id']}) - HAS ASSIGNMENT")

print(f"\n=== Available staff for Monday Period 1 (excluding Velmurugan) ===")
cursor.execute('''
    SELECT s.id, s.full_name, s.department
    FROM staff s
    WHERE s.school_id = ? 
        AND s.department = ?
        AND s.id != ?
        AND s.id NOT IN (
            SELECT staff_id FROM timetable_hierarchical_assignments 
            WHERE school_id = ? 
                AND day_of_week = ? 
                AND period_number = ?
            UNION
            SELECT staff_id FROM timetable_self_allocations
            WHERE school_id = ? 
                AND day_of_week = ? 
                AND period_number = ?
        )
    ORDER BY s.full_name
''', (school_id, department, current_user_id,
      school_id, day_of_week, period_number,
      school_id, day_of_week, period_number))

available_staff = cursor.fetchall()
print(f"Found {len(available_staff)} available:")
for s in available_staff:
    print(f"  {s['full_name']} (ID: {s['id']})")

db.close()
