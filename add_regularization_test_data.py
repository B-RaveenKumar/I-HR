#!/usr/bin/env python3
"""
Add Sample Attendance Records with Late Arrivals and Early Departures
This script queries the existing MySQL database and adds test regularization attendance data
"""

import sys
from datetime import datetime, timedelta
from app import app
from database import get_db

def add_sample_attendance():
    """Add sample attendance records with late arrivals and early departures"""
    
    # Create Flask application context
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        # Get first available staff
        cursor.execute("SELECT id, staff_id FROM staff LIMIT 1")
        staff_row = cursor.fetchone()
        if not staff_row:
            print("❌ No staff found. Please add staff first.")
            return
        
        staff_db_id, staff_login_id = staff_row[0], staff_row[1]
        
        # Get first available school
        cursor.execute("SELECT id FROM schools LIMIT 1")
        school_row = cursor.fetchone()
        if not school_row:
            print("❌ No schools found. Please add a school first.")
            return
        
        school_id = school_row[0]
        
        print(f"✓ Using staff: {staff_login_id} (ID: {staff_db_id}), school_id: {school_id}")
        
        # Get today and calculate date range for last 7 days
        today = datetime.now().date()
        
        # Sample attendance records with late arrivals and early departures
        sample_records = [
            {
                'date': (today - timedelta(days=1)).isoformat(),
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
                'date': (today - timedelta(days=2)).isoformat(),
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
                'date': (today - timedelta(days=3)).isoformat(),
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
                'date': (today - timedelta(days=4)).isoformat(),
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
                'date': (today - timedelta(days=5)).isoformat(),
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
                # Use INSERT IGNORE or check if record exists
                cursor.execute('''
                    INSERT INTO attendance 
                    (staff_id, school_id, date, time_in, time_out, shift_start_time, shift_end_time,
                     late_duration_minutes, early_departure_minutes, status, shift_type)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    staff_db_id,
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
                print(f"⚠ Skipped record for {record['date']} (may already exist): {e}")
        
        db.commit()
        db.close()
        
        print(f"\n✅ Successfully added {inserted} sample attendance records with late/early indicators")
        print("   These records are now available in the regularization form")

if __name__ == '__main__':
    add_sample_attendance()
