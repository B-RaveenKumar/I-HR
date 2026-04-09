#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
from datetime import datetime, timedelta
os.chdir('d:\\SMproject\\I-HR')
sys.path.insert(0, 'd:\\SMproject\\I-HR')

from app import app

with app.app_context():
    from database import get_db
    db = get_db()
    cursor = db.cursor()
    
    print('\n=== SCHOOL 5 REGULARIZATION DIAGNOSIS ===\n')
    
    # Check staff in school 5
    print('STAFF IN SCHOOL 5:')
    cursor.execute('SELECT id, staff_id, full_name FROM staff WHERE school_id = 5 LIMIT 10')
    staff_list = cursor.fetchall()
    if staff_list:
        for s in staff_list:
            print(f'  DB_ID={s[0]}, LOGIN_ID={s[1]}, NAME={s[2]}')
    else:
        print('  ERROR: No staff found')
    
    # Check attendance
    print('\nATTENDANCE RECORDS IN SCHOOL 5 (last 7 days with late/early):')
    today = datetime.now().date()
    lookback = today - timedelta(days=7)
    
    cursor.execute('''
        SELECT id, staff_id, date, late_duration_minutes, early_departure_minutes, status
        FROM attendance 
        WHERE school_id = 5 AND date >= %s
              AND (late_duration_minutes > 0 OR early_departure_minutes > 0)
        ORDER BY date DESC
        LIMIT 15
    ''', (lookback,))
    records = cursor.fetchall()
    print(f"  Found {len(records) if records else 0} records")
    if records:
        for r in records:
            print(f'    ID={r[0]}, Staff={r[1]}, Date={r[2]}, Late={r[3]}m, Early={r[4]}m, Status={r[5]}')
    
    # Check recent reqs
    print('\nRECENT REGULARIZATION REQUESTS IN SCHOOL 5:')
    cursor.execute('''
        SELECT r.id, r.staff_id, r.request_type, r.status, r.requested_at
        FROM attendance_regularization_requests r
        WHERE r.school_id = 5
        ORDER BY r.requested_at DESC
        LIMIT 10
    ''')
    reqs = cursor.fetchall()
    print(f"  Found {len(reqs) if reqs else 0} requests")
    if reqs:
        for req in reqs:
            print(f'    REQ_ID={req[0]}, Staff={req[1]}, Type={req[2]}, Status={req[3]}, When={req[4]}')
    
    db.close()

