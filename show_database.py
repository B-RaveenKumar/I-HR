import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'vishnorex.db')
db = sqlite3.connect(db_path)
cursor = db.cursor()

print('=' * 80)
print('DATABASE INVENTORY - REAL DATA')
print('=' * 80)

# 1. Get all schools
print('\n📚 SCHOOLS IN DATABASE')
print('-' * 80)
cursor.execute('SELECT id, name, address, contact_email, contact_phone FROM schools')
schools = cursor.fetchall()
print(f'Total Schools: {len(schools)}\n')
for school in schools:
    print(f'  ID: {school[0]:3} | Name: {school[1]:30} | Email: {school[3]}')
    if school[2]:
        print(f'        Address: {school[2]}')
    if school[4]:
        print(f'        Phone: {school[4]}')
    print()

# 2. Get all staff
print('\n👥 STAFF IN DATABASE')
print('-' * 80)
cursor.execute('''
    SELECT id, school_id, full_name, department, position, email 
    FROM staff 
    ORDER BY school_id, full_name
    LIMIT 50
''')
staff_list = cursor.fetchall()
print(f'Total Staff: {len(staff_list)}\n')

current_school = None
for staff in staff_list:
    if staff[1] != current_school:
        current_school = staff[1]
        cursor.execute('SELECT name FROM schools WHERE id = ?', (current_school,))
        school_name = cursor.fetchone()
        if school_name:
            print(f'\n  School ID {current_school}: {school_name[0]}')
    
    print(f'    ID: {staff[0]:3} | {staff[2]:25} | {staff[3]:15} | {staff[4]:20}')

# 3. Get all departments
print('\n\n🏢 DEPARTMENTS IN DATABASE')
print('-' * 80)
cursor.execute('''
    SELECT DISTINCT school_id, department FROM staff 
    WHERE department IS NOT NULL AND department != ''
    ORDER BY school_id, department
''')
departments = cursor.fetchall()
print(f'Total Unique Departments: {len(departments)}\n')

current_school = None
for dept in departments:
    if dept[0] != current_school:
        current_school = dept[0]
        cursor.execute('SELECT name FROM schools WHERE id = ?', (current_school,))
        school_name = cursor.fetchone()
        if school_name:
            print(f'\n  School ID {current_school}: {school_name[0]}')
    
    # Count staff in this department
    cursor.execute('SELECT COUNT(*) FROM staff WHERE school_id = ? AND department = ?', 
                   (dept[0], dept[1]))
    count = cursor.fetchone()[0]
    print(f'    • {dept[1]:20} ({count} staff)')

# 4. Check admins
print('\n\n🔑 ADMINS IN DATABASE')
print('-' * 80)
cursor.execute('''
    SELECT id, school_id, username, full_name, email 
    FROM admins 
    ORDER BY school_id
''')
admins = cursor.fetchall()
print(f'Total Admins: {len(admins)}\n')
for admin in admins:
    cursor.execute('SELECT name FROM schools WHERE id = ?', (admin[1],))
    school_name = cursor.fetchone()
    school_str = school_name[0] if school_name else f'School ID {admin[1]}'
    print(f'  ID: {admin[0]:3} | Username: {admin[2]:20} | School: {school_str:30} | {admin[3]}')

# 5. Timetable status
print('\n\n📅 TIMETABLE STATUS')
print('-' * 80)
cursor.execute('SELECT school_id, is_enabled, number_of_periods FROM timetable_settings')
timetable = cursor.fetchall()
if timetable:
    for t in timetable:
        cursor.execute('SELECT name FROM schools WHERE id = ?', (t[0],))
        school_name = cursor.fetchone()
        school_str = school_name[0] if school_name else f'School ID {t[0]}'
        status = '✅ ENABLED' if t[1] else '❌ DISABLED'
        print(f'  {school_str:30} - {status} ({t[2]} periods)')
else:
    print('  No timetable settings configured yet')

print('\n' + '=' * 80)
db.close()
