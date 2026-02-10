"""
Populate database with realistic sample data for timetable testing
"""
from app import app
from database import get_db
from timetable_manager import TimetableManager
import sqlite3

with app.app_context():
    db = get_db()
    cursor = db.cursor()
    
    print('🔄 POPULATING DATABASE WITH SAMPLE DATA\n')
    
    # 1. Clear existing test data
    print('Clearing old test school...')
    cursor.execute('DELETE FROM schools WHERE id = 1')
    db.commit()
    
    # 2. Add realistic schools
    print('\n📚 Adding Schools...')
    schools_data = [
        ('Central High School', '123 Main Street, Downtown', 'admin@centralhs.edu', '555-0001'),
        ('St. Mary\'s Academy', '456 Oak Avenue, North Side', 'info@stmaryacademy.edu', '555-0002'),
        ('Lincoln University Prep', '789 Elm Road, East District', 'support@lincolnprep.edu', '555-0003'),
        ('Valley Middle School', '321 Pine Lane, West Valley', 'contact@valleymiddle.edu', '555-0004'),
        ('Harbor Technical Institute', '654 Beach Boulevard, Waterfront', 'admin@harbortech.edu', '555-0005'),
    ]
    
    school_ids = {}
    for name, address, email, phone in schools_data:
        cursor.execute('''
            INSERT INTO schools (name, address, contact_email, contact_phone)
            VALUES (?, ?, ?, ?)
        ''', (name, address, email, phone))
        db.commit()
        school_id = cursor.lastrowid
        school_ids[name] = school_id
        print(f'  ✓ {name} (ID: {school_id})')
    
    # 3. Add admins for each school
    print('\n🔑 Adding Admins...')
    for idx, (school_name, school_id) in enumerate(school_ids.items(), 1):
        username = f'admin{idx}'
        password_hash = 'test123'  # In production, use hashed passwords
        full_name = f'Principal {idx}'
        email = f'admin{idx}@school.edu'
        
        cursor.execute('''
            INSERT INTO admins (school_id, username, password, full_name, email)
            VALUES (?, ?, ?, ?, ?)
        ''', (school_id, username, password_hash, full_name, email))
        db.commit()
        print(f'  ✓ {username} → {school_name}')
    
    # 4. Add departments and staff for each school
    print('\n👥 Adding Staff & Departments...')
    departments = ['English', 'Mathematics', 'Science', 'History', 'Physical Education', 'Arts', 'Technology', 'Library']
    positions = ['Teacher', 'Senior Teacher', 'Department Head', 'Lecturer']
    
    for school_name, school_id in school_ids.items():
        print(f'\n  {school_name}:')
        
        # Add 3 staff per department
        for dept_idx, dept in enumerate(departments, 1):
            for staff_idx in range(1, 4):
                staff_id = f'{school_id}-{dept_idx:02d}-{staff_idx:02d}'
                first_name = ['John', 'Sarah', 'Michael', 'Emma', 'David', 'Lisa', 'Robert', 'Jennifer'][staff_idx % 8]
                last_name = ['Smith', 'Johnson', 'Williams', 'Brown', 'Davis', 'Miller', 'Wilson', 'Moore'][dept_idx % 8]
                full_name = f'{first_name} {last_name}'
                position = positions[staff_idx % len(positions)]
                email = f'{first_name.lower()}.{last_name.lower()}@{school_name.lower().replace(" ", "")}.edu'
                
                cursor.execute('''
                    INSERT INTO staff 
                    (school_id, staff_id, full_name, first_name, last_name, email, department, position, password)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (school_id, staff_id, full_name, first_name, last_name, email, dept, position, 'test123'))
                db.commit()
            
            print(f'    • {dept}: 3 staff added')
    
    # 5. Enable timetable for all schools
    print('\n📅 Enabling Timetable for All Schools...')
    for school_name, school_id in school_ids.items():
        result = TimetableManager.enable_timetable_for_school(school_id, True)
        print(f'  ✓ {school_name} (ID: {school_id})')
    
    # 6. Add periods for each school
    print('\n⏰ Adding Time Periods for All Schools...')
    periods_config = [
        (1, 'Period 1', '09:00', '09:45'),
        (2, 'Period 2', '09:45', '10:30'),
        (3, 'Period 3', '10:30', '11:15'),
        (4, 'Period 4', '11:15', '12:00'),
        (5, 'Lunch', '12:00', '12:45'),
        (6, 'Period 5', '12:45', '13:30'),
        (7, 'Period 6', '13:30', '14:15'),
        (8, 'Period 7', '14:15', '15:00'),
    ]
    
    for school_id in school_ids.values():
        for period_num, period_name, start_time, end_time in periods_config:
            TimetableManager.add_period(school_id, period_num, period_name, start_time, end_time)
    
    print(f'  ✓ 8 periods added for each school')
    
    # 7. Set department permissions for each school
    print('\n🔐 Setting Department Permissions...')
    for school_id in school_ids.values():
        for dept in departments:
            TimetableManager.set_department_permission(school_id, dept, True, True)
    
    print(f'  ✓ Permissions set for all departments')
    
    # 8. Add sample timetable assignments
    print('\n📋 Adding Sample Timetable Assignments...')
    import random
    
    assignment_count = 0
    for school_id in school_ids.values():
        # Get staff for this school
        cursor.execute('SELECT id FROM staff WHERE school_id = ?', (school_id,))
        staff_members = cursor.fetchall()
        
        # Assign each staff member to 4-6 random periods
        for staff in staff_members:
            staff_id = staff[0]
            num_assignments = random.randint(4, 6)
            assigned_periods = random.sample(range(1, 9), num_assignments)
            
            for day in range(6):  # Monday-Saturday
                period = random.choice(assigned_periods)
                
                cursor.execute('''
                    SELECT department FROM staff WHERE id = ?
                ''', (staff_id,))
                dept = cursor.fetchone()[0]
                
                cursor.execute('''
                    INSERT OR IGNORE INTO timetable_assignments
                    (school_id, staff_id, day_of_week, period_number, class_subject, is_assigned)
                    VALUES (?, ?, ?, ?, ?, 1)
                ''', (school_id, staff_id, day, period, f'{dept} Class'))
                
                assignment_count += 1
        
        db.commit()
    
    print(f'  ✓ {assignment_count} assignments created')
    
    # Final summary
    print('\n' + '=' * 80)
    print('✅ DATABASE POPULATION COMPLETE!')
    print('=' * 80)
    
    cursor.execute('SELECT COUNT(*) FROM schools')
    school_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM admins')
    admin_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM staff')
    staff_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM timetable_periods')
    period_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM timetable_assignments')
    assignment_count = cursor.fetchone()[0]
    
    print(f'\n📊 SUMMARY:')
    print(f'   Schools:    {school_count}')
    print(f'   Admins:     {admin_count}')
    print(f'   Staff:      {staff_count}')
    print(f'   Periods:    {period_count}')
    print(f'   Assignments: {assignment_count}')
    
    print(f'\n🎯 NEXT STEPS:')
    print(f'   1. Start Flask: python app.py')
    print(f'   2. Login with admin1, admin2, etc.')
    print(f'   3. Access timetable features')
    print(f'   4. Use staff credentials to view personal schedules')
    
    print('\n' + '=' * 80)
