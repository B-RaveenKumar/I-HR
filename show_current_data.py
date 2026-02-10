import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'vishnorex.db')
db = sqlite3.connect(db_path)
cursor = db.cursor()

print('=' * 70)
print('CURRENT DATABASE STATE - YOUR REAL DATA')
print('=' * 70)

# Schools
print('\n📚 SCHOOLS')
cursor.execute('SELECT id, name, address, contact_email FROM schools')
schools = cursor.fetchall()
if schools:
    for s in schools:
        print(f'  ID {s[0]}: {s[1]} - {s[3]}')
else:
    print('  ⚠️  No schools found')

# Admins
print('\n🔑 ADMINS')
cursor.execute('SELECT id, username, full_name, school_id FROM admins')
admins = cursor.fetchall()
if admins:
    for a in admins:
        print(f'  {a[1]:15} | {a[2]:25} | School ID: {a[3]}')
else:
    print('  ⚠️  No admins found')

# Staff
print('\n👥 STAFF')
cursor.execute('SELECT COUNT(DISTINCT school_id) as schools, COUNT(*) as total FROM staff')
result = cursor.fetchone()
print(f'  Total: {result[1]} staff')
print(f'  Schools: {result[0]}')

cursor.execute('''
SELECT school_id, COUNT(*) as count, GROUP_CONCAT(DISTINCT department, ', ') as departments
FROM staff
GROUP BY school_id
''')
for school_id, count, departments in cursor.fetchall():
    print(f'  School ID {school_id}: {count} staff - Departments: {departments}')

# Timetable status
print('\n📅 TIMETABLE STATUS')
cursor.execute('SELECT school_id, is_enabled FROM timetable_settings WHERE is_enabled = 1')
enabled = cursor.fetchall()
if enabled:
    print(f'  {len(enabled)} school(s) have timetable enabled')
    for school_id, _ in enabled:
        cursor.execute('SELECT COUNT(*) FROM timetable_periods WHERE school_id = ?', (school_id,))
        period_count = cursor.fetchone()[0]
        print(f'    - School ID {school_id}: {period_count} periods')
else:
    print('  No schools have timetable enabled yet')

# Check if we need to enable timetable for existing schools
print('\n💡 NEXT STEPS:')
cursor.execute('SELECT id FROM schools')
school_ids = [s[0] for s in cursor.fetchall()]
if school_ids:
    print(f'  Your schools: {school_ids}')
    print(f'  Enable timetable for them using the app interface')
else:
    print('  ⚠️  No schools in database - check your backup')

print('\n' + '=' * 70)

db.close()
