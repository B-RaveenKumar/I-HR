#!/usr/bin/env python3
"""
Diagnose School 5 Regularization Issues
"""

from app import app
from datetime import datetime, timedelta

with app.app_context():
    from database import get_db
    db = get_db()
    cursor = db.cursor()
    
    print('\n' + '='*70)
    print('SCHOOL 5 REGULARIZATION DIAGNOSIS')
    print('='*70)
    
    # Check staff in school 5
    print('\n✓ STAFF IN SCHOOL 5:')
    print('-'*70)
    cursor.execute('SELECT id, staff_id, name FROM staff WHERE school_id = 5 LIMIT 10')
    staff_list = cursor.fetchall()
    if staff_list:
        for s in staff_list:
            print(f'  DB ID: {s[0]:3d} | Login ID: {s[1]:10s} | Name: {s[2]}')
    else:
        print('  ✗ No staff found in school 5')
    
    # Check attendance records
    print('\n✓ ATTENDANCE RECORDS IN SCHOOL 5 (last 7 days with late/early):')
    print('-'*70)
    today = datetime.now().date()
    lookback = today - timedelta(days=7)
    
    cursor.execute('''
        SELECT id, staff_id, date, time_in, time_out, 
               late_duration_minutes, early_departure_minutes, status
        FROM attendance 
        WHERE school_id = 5 AND date >= %s
              AND (late_duration_minutes > 0 OR early_departure_minutes > 0)
        ORDER BY date DESC
        LIMIT 15
    ''', (lookback,))
    records = cursor.fetchall()
    if records:
        for r in records:
            print(f'  ID: {r[0]:3d} | Staff: {r[1]:3d} | Date: {r[2]} | '
                  f'In: {r[3]} | Out: {r[4]} | Late: {r[5]:2d}m | Early: {r[6]:2d}m | {r[7]}')
    else:
        print('  ✗ No eligible attendance records found')
    
    # Check recent regularization requests for school 5
    print('\n✓ RECENT REGULARIZATION REQUESTS IN SCHOOL 5:')
    print('-'*70)
    cursor.execute('''
        SELECT r.id, r.staff_id, r.request_type, r.status, r.requested_at, r.admin_reason
        FROM attendance_regularization_requests r
        WHERE r.school_id = 5
        ORDER BY r.requested_at DESC
        LIMIT 10
    ''')
    reqs = cursor.fetchall()
    if reqs:
        for req in reqs:
            print(f'  Req ID: {req[0]:3d} | Staff: {req[1]:3d} | Type: {req[2]:15s} | '
                  f'Status: {req[3]:8s} | Requested: {req[4]} | Admin: {req[5]}')
    else:
        print('  ✓ No regularization requests found yet')
    
    # Show the regularization_candidates query for a sample staff
    print('\n✓ SAMPLE REGULARIZATION CANDIDATES QUERY:')
    print('-'*70)
    if staff_list:
        sample_staff_id = staff_list[0][0]
        sample_staff_login = staff_list[0][1]
        print(f'  Testing with Staff DB ID: {sample_staff_id}, Login ID: {sample_staff_login}')
        
        cursor.execute('''
            SELECT id, date, time_in, time_out, status,
                   late_duration_minutes, early_departure_minutes,
                   shift_start_time, shift_end_time
            FROM attendance
            WHERE staff_id = %s
              AND school_id = 5
              AND date BETWEEN %s AND %s
              AND COALESCE(regularization_status, '') != 'pending'
              AND (
                    (COALESCE(late_duration_minutes, 0) > 0 AND time_in IS NOT NULL)
                    OR
                    (COALESCE(early_departure_minutes, 0) > 0 AND time_out IS NOT NULL)
              )
            ORDER BY date DESC
        ''', (sample_staff_id, lookback, today))
        candidates = cursor.fetchall()
        if candidates:
            print(f'  Found {len(candidates)} eligible records:')
            for c in candidates:
                print(f'    ID: {c[0]:3d} | Date: {c[1]} | Late: {c[5]:2d}m | Early: {c[6]:2d}m')
        else:
            print('  ✗ No eligible records for this staff')
    
    db.close()

print('\n' + '='*70)
