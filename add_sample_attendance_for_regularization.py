#!/usr/bin/env python3
"""
Add Sample Attendance Records with Late Arrivals and Early Departures
This script adds test attendance records for testing the regularization feature
"""

import sqlite3
from datetime import datetime, timedelta
import os

def add_sample_attendance():
    """Add sample attendance records with late arrivals and early departures"""
    
    # Connect to database
    db_path = 'attendance.db'
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get first available staff and school
    cursor.execute("SELECT id FROM staff LIMIT 1")
    staff_row = cursor.fetchone()
    if not staff_row:
        print("❌ No staff found. Please add staff first.")
        conn.close()
        return
    
    staff_id = staff_row[0]
    
    cursor.execute("SELECT id FROM schools LIMIT 1")
    school_row = cursor.fetchone()
    if not school_row:
        print("❌ No schools found. Please add a school first.")
        conn.close()
        return
    
    school_id = school_row[0]
    
    print(f"✓ Using staff_id: {staff_id}, school_id: {school_id}")
    
    # Get today and calculate date range for last 7 days
    today = datetime.now()
    
    # Sample attendance records with late arrivals and early departures
    sample_records = [
        {
            'date': (today - timedelta(days=1)).strftime('%Y-%m-%d'),
            'time_in': '10:30:00',  # 30 minutes late
            'time_out': '17:00:00',
            'shift_start_time': '10:00:00',
            'shift_end_time': '18:00:00',
            'late_duration_minutes': 30,
            'early_departure_minutes': 0,
            'status': 'late',
            'shift_type': 'general',
        },
        {
            'date': (today - timedelta(days=2)).strftime('%Y-%m-%d'),
            'time_in': '09:45:00',
            'time_out': '16:30:00',  # 30 minutes early
            'shift_start_time': '09:30:00',
            'shift_end_time': '17:00:00',
            'late_duration_minutes': 0,
            'early_departure_minutes': 30,
            'status': 'left_soon',
            'shift_type': 'general',
        },
        {
            'date': (today - timedelta(days=3)).strftime('%Y-%m-%d'),
            'time_in': '10:15:00',  # 15 minutes late
            'time_out': '17:15:00',
            'shift_start_time': '10:00:00',
            'shift_end_time': '18:00:00',
            'late_duration_minutes': 15,
            'early_departure_minutes': 0,
            'status': 'late',
            'shift_type': 'general',
        },
        {
            'date': (today - timedelta(days=4)).strftime('%Y-%m-%d'),
            'time_in': '09:50:00',
            'time_out': '16:45:00',  # 15 minutes early
            'shift_start_time': '09:30:00',
            'shift_end_time': '17:00:00',
            'late_duration_minutes': 0,
            'early_departure_minutes': 15,
            'status': 'left_soon',
            'shift_type': 'general',
        },
        {
            'date': (today - timedelta(days=5)).strftime('%Y-%m-%d'),
            'time_in': '10:45:00',  # 45 minutes late
            'time_out': '18:00:00',
            'shift_start_time': '10:00:00',
            'shift_end_time': '18:00:00',
            'late_duration_minutes': 45,
            'early_departure_minutes': 0,
            'status': 'late',
            'shift_type': 'general',
        },
    ]
    
    # Insert records
    inserted = 0
    for record in sample_records:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO attendance 
                (staff_id, school_id, date, time_in, time_out, shift_start_time, shift_end_time,
                 late_duration_minutes, early_departure_minutes, status, shift_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                staff_id,
                school_id,
                record['date'],
                record['time_in'],
                record['time_out'],
                record['shift_start_time'],
                record['shift_end_time'],
                record['late_duration_minutes'],
                record['early_departure_minutes'],
                record['status'],
                record['shift_type'],
            ))
            inserted += 1
            print(f"✓ Added attendance record for {record['date']}: {record['status']} "
                  f"(Late: {record['late_duration_minutes']}m, Early: {record['early_departure_minutes']}m)")
        except Exception as e:
            print(f"✗ Error adding record for {record['date']}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Successfully added {inserted} sample attendance records with late/early indicators")
    print("   These records are now available in the regularization form")

if __name__ == '__main__':
    add_sample_attendance()
