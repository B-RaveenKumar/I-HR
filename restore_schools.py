"""
Restore schools that are referenced by existing admins and staff
"""
from app import app
from database import get_db
from timetable_manager import TimetableManager

with app.app_context():
    db = get_db()
    cursor = db.cursor()
    
    print('🔧 RESTORING SCHOOL DATA\n')
    
    # Restore the schools that admins and staff are linked to
    schools_data = [
        (2, 'Central High School', '123 Main Street, Downtown', 'admin@centralhs.edu', '555-0001'),
        (3, 'St. Mary\'s Academy', '456 Oak Avenue, North Side', 'info@stmaryacademy.edu', '555-0002'),
        (4, 'Lincoln University Prep', '789 Elm Road, East District', 'support@lincolnprep.edu', '555-0003'),
        (5, 'Valley Middle School', '321 Pine Lane, West Valley', 'contact@valleymiddle.edu', '555-0004'),
        (6, 'Harbor Technical Institute', '654 Beach Boulevard, Waterfront', 'admin@harbortech.edu', '555-0005'),
    ]
    
    print('Adding schools...')
    for school_id, name, address, email, phone in schools_data:
        cursor.execute('''
            INSERT OR REPLACE INTO schools (id, name, address, contact_email, contact_phone)
            VALUES (?, ?, ?, ?, ?)
        ''', (school_id, name, address, email, phone))
        db.commit()
        print(f'  ✓ ID {school_id}: {name}')
    
    print('\n📊 CURRENT STATE')
    print('-' * 60)
    
    # Verify
    cursor.execute('SELECT COUNT(*) FROM schools')
    school_count = cursor.fetchone()[0]
    print(f'Schools: {school_count}')
    
    cursor.execute('SELECT COUNT(*) FROM admins')
    admin_count = cursor.fetchone()[0]
    print(f'Admins: {admin_count}')
    
    cursor.execute('SELECT COUNT(*) FROM staff')
    staff_count = cursor.fetchone()[0]
    print(f'Staff: {staff_count}')
    
    cursor.execute('SELECT COUNT(*) FROM timetable_periods')
    period_count = cursor.fetchone()[0]
    print(f'Periods: {period_count}')
    
    cursor.execute('SELECT COUNT(*) FROM timetable_assignments')
    assign_count = cursor.fetchone()[0]
    print(f'Assignments: {assign_count}')
    
    print('\n✅ DATABASE READY')
    print('   Your real data with timetable system integrated')

print('\n📝 NOTE: Do NOT run populate_db.py')
print('   This database has real staff/admin data')
