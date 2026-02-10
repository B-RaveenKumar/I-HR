# attendance_advanced.py
"""
Advanced Attendance Management System

This module provides enhanced attendance features including:
- Overtime tracking and management
- Advanced shift management
- Attendance regularization
- Leave integration
- Biometric device integration
- Attendance analytics and reporting
"""

import sqlite3
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple
from database import get_db
from shift_management import ShiftManager
import json


class AdvancedAttendanceManager:
    """Advanced attendance management with overtime and enhanced features"""
    
    def __init__(self):
        self.shift_manager = ShiftManager()
        self.overtime_threshold_hours = 8  # Standard work hours
        self.max_overtime_hours = 4  # Maximum overtime per day
    
    def process_attendance_with_overtime(self, staff_id: int, school_id: int, 
                                       verification_type: str, timestamp: datetime) -> Dict:
        """Process attendance with overtime calculation"""
        try:
            db = get_db()
            today = timestamp.date()
            current_time = timestamp.time()
            
            # Get staff shift information
            staff = db.execute('SELECT shift_type FROM staff WHERE id = ?', (staff_id,)).fetchone()
            shift_type = staff['shift_type'] if staff else 'general'
            
            # Get existing attendance record
            existing = db.execute('''
                SELECT * FROM attendance WHERE staff_id = ? AND date = ?
            ''', (staff_id, today)).fetchone()
            
            if verification_type == 'check-in':
                return self._process_check_in_with_overtime(
                    staff_id, school_id, today, current_time, shift_type, existing
                )
            elif verification_type == 'check-out':
                return self._process_check_out_with_overtime(
                    staff_id, school_id, today, current_time, shift_type, existing
                )
            elif verification_type == 'overtime-in':
                return self._process_overtime_in(
                    staff_id, school_id, today, current_time, existing
                )
            elif verification_type == 'overtime-out':
                return self._process_overtime_out(
                    staff_id, school_id, today, current_time, existing
                )
            else:
                return {'success': False, 'error': 'Invalid verification type'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _process_check_in_with_overtime(self, staff_id: int, school_id: int, 
                                      date: datetime.date, time_in: time, 
                                      shift_type: str, existing: Optional[Dict]) -> Dict:
        """Process check-in with shift calculations"""
        db = get_db()
        
        # Calculate attendance status using shift manager
        attendance_result = self.shift_manager.calculate_attendance_status(shift_type, time_in)
        
        if existing:
            # Update existing record
            db.execute('''
                UPDATE attendance SET 
                    time_in = ?, status = ?, late_duration_minutes = ?,
                    shift_start_time = ?, shift_end_time = ?
                WHERE staff_id = ? AND date = ?
            ''', (
                time_in.strftime('%H:%M:%S'),
                attendance_result['status'],
                attendance_result['late_duration_minutes'],
                attendance_result['shift_start_time'].strftime('%H:%M:%S'),
                attendance_result['shift_end_time'].strftime('%H:%M:%S'),
                staff_id, date
            ))
        else:
            # Create new record
            db.execute('''
                INSERT INTO attendance (
                    staff_id, school_id, date, time_in, status,
                    late_duration_minutes, shift_start_time, shift_end_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                staff_id, school_id, date,
                time_in.strftime('%H:%M:%S'),
                attendance_result['status'],
                attendance_result['late_duration_minutes'],
                attendance_result['shift_start_time'].strftime('%H:%M:%S'),
                attendance_result['shift_end_time'].strftime('%H:%M:%S')
            ))
        
        db.commit()
        
        return {
            'success': True,
            'action': 'check-in',
            'status': attendance_result['status'],
            'late_minutes': attendance_result['late_duration_minutes'],
            'message': f"Check-in recorded at {time_in.strftime('%I:%M %p')}"
        }
    
    def _process_check_out_with_overtime(self, staff_id: int, school_id: int,
                                       date: datetime.date, time_out: time,
                                       shift_type: str, existing: Optional[Dict]) -> Dict:
        """Process check-out with overtime calculation"""
        db = get_db()
        
        if not existing:
            # Create record with check-out only
            db.execute('''
                INSERT INTO attendance (staff_id, school_id, date, time_out, status)
                VALUES (?, ?, ?, ?, 'present')
            ''', (staff_id, school_id, date, time_out.strftime('%H:%M:%S')))
            db.commit()
            
            return {
                'success': True,
                'action': 'check-out',
                'message': f"Check-out recorded at {time_out.strftime('%I:%M %p')}"
            }
        
        # Calculate work hours and overtime
        time_in_str = existing['time_in']
        if time_in_str:
            time_in = datetime.strptime(time_in_str, '%H:%M:%S').time()
            work_hours = self._calculate_work_hours(time_in, time_out)
            overtime_hours = max(0, work_hours - self.overtime_threshold_hours)
            
            # Determine final status
            shift_end_time = datetime.strptime(existing['shift_end_time'], '%H:%M:%S').time() if existing['shift_end_time'] else time(17, 0)
            early_departure_minutes = 0
            
            if time_out < shift_end_time:
                early_departure_minutes = int((datetime.combine(date, shift_end_time) - 
                                             datetime.combine(date, time_out)).total_seconds() / 60)
            
            final_status = existing['status']
            if early_departure_minutes > 30:  # Left more than 30 minutes early
                final_status = 'left_soon'
        else:
            work_hours = 0
            overtime_hours = 0
            early_departure_minutes = 0
            final_status = 'present'
        
        # Update attendance record
        db.execute('''
            UPDATE attendance SET 
                time_out = ?, status = ?, work_hours = ?, overtime_hours = ?,
                early_departure_minutes = ?
            WHERE staff_id = ? AND date = ?
        ''', (
            time_out.strftime('%H:%M:%S'),
            final_status,
            work_hours,
            overtime_hours,
            early_departure_minutes,
            staff_id, date
        ))
        
        db.commit()
        
        return {
            'success': True,
            'action': 'check-out',
            'work_hours': work_hours,
            'overtime_hours': overtime_hours,
            'message': f"Check-out recorded at {time_out.strftime('%I:%M %p')}. Work hours: {work_hours:.1f}, Overtime: {overtime_hours:.1f}"
        }
    
    def _process_overtime_in(self, staff_id: int, school_id: int,
                           date: datetime.date, overtime_in: time,
                           existing: Optional[Dict]) -> Dict:
        """Process overtime check-in"""
        db = get_db()
        
        if not existing:
            return {'success': False, 'error': 'No regular attendance record found for today'}
        
        if not existing['time_out']:
            return {'success': False, 'error': 'Please check out from regular shift first'}
        
        # Update overtime in time
        db.execute('''
            UPDATE attendance SET overtime_in = ?
            WHERE staff_id = ? AND date = ?
        ''', (overtime_in.strftime('%H:%M:%S'), staff_id, date))
        
        db.commit()
        
        return {
            'success': True,
            'action': 'overtime-in',
            'message': f"Overtime started at {overtime_in.strftime('%I:%M %p')}"
        }
    
    def _process_overtime_out(self, staff_id: int, school_id: int,
                            date: datetime.date, overtime_out: time,
                            existing: Optional[Dict]) -> Dict:
        """Process overtime check-out"""
        db = get_db()
        
        if not existing or not existing['overtime_in']:
            return {'success': False, 'error': 'No overtime check-in found for today'}
        
        # Calculate overtime hours
        overtime_in = datetime.strptime(existing['overtime_in'], '%H:%M:%S').time()
        overtime_hours = self._calculate_work_hours(overtime_in, overtime_out)
        
        # Validate overtime hours
        if overtime_hours > self.max_overtime_hours:
            return {
                'success': False, 
                'error': f'Overtime cannot exceed {self.max_overtime_hours} hours per day'
            }
        
        # Update total overtime hours
        total_overtime = (existing['overtime_hours'] or 0) + overtime_hours
        
        # Update attendance record
        db.execute('''
            UPDATE attendance SET 
                overtime_out = ?, overtime_hours = ?
            WHERE staff_id = ? AND date = ?
        ''', (overtime_out.strftime('%H:%M:%S'), total_overtime, staff_id, date))
        
        db.commit()
        
        return {
            'success': True,
            'action': 'overtime-out',
            'overtime_hours': overtime_hours,
            'total_overtime': total_overtime,
            'message': f"Overtime ended at {overtime_out.strftime('%I:%M %p')}. Overtime hours: {overtime_hours:.1f}"
        }
    
    def _calculate_work_hours(self, start_time: time, end_time: time) -> float:
        """Calculate work hours between two times"""
        start_dt = datetime.combine(datetime.today(), start_time)
        end_dt = datetime.combine(datetime.today(), end_time)
        
        # Handle next day scenario
        if end_dt < start_dt:
            end_dt += timedelta(days=1)
        
        duration = end_dt - start_dt
        return duration.total_seconds() / 3600
    
    def get_overtime_summary(self, staff_id: int, start_date: str, end_date: str) -> Dict:
        """Get overtime summary for a staff member"""
        db = get_db()
        
        overtime_data = db.execute('''
            SELECT date, overtime_hours, work_hours, time_in, time_out, overtime_in, overtime_out
            FROM attendance
            WHERE staff_id = ? AND date BETWEEN ? AND ?
            AND overtime_hours > 0
            ORDER BY date DESC
        ''', (staff_id, start_date, end_date)).fetchall()
        
        total_overtime = sum(record['overtime_hours'] or 0 for record in overtime_data)
        total_days_with_overtime = len(overtime_data)
        
        return {
            'success': True,
            'total_overtime_hours': total_overtime,
            'total_days_with_overtime': total_days_with_overtime,
            'average_overtime_per_day': total_overtime / total_days_with_overtime if total_days_with_overtime > 0 else 0,
            'overtime_records': [dict(record) for record in overtime_data]
        }
    
    def create_attendance_regularization_request(self, staff_id: int, school_id: int,
                                               attendance_id: int, request_type: str,
                                               original_time: str, expected_time: str,
                                               reason: str) -> Dict:
        """Create attendance regularization request"""
        try:
            db = get_db()
            
            # Calculate duration difference
            orig_time = datetime.strptime(original_time, '%H:%M:%S').time()
            exp_time = datetime.strptime(expected_time, '%H:%M:%S').time()
            
            orig_dt = datetime.combine(datetime.today(), orig_time)
            exp_dt = datetime.combine(datetime.today(), exp_time)
            
            duration_minutes = int(abs((exp_dt - orig_dt).total_seconds() / 60))
            
            # Insert regularization request
            cursor = db.execute('''
                INSERT INTO attendance_regularization_requests (
                    attendance_id, staff_id, school_id, request_type,
                    original_time, expected_time, duration_minutes, staff_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (attendance_id, staff_id, school_id, request_type,
                  original_time, expected_time, duration_minutes, reason))
            
            request_id = cursor.lastrowid
            
            # Update attendance record to mark regularization requested
            db.execute('''
                UPDATE attendance SET 
                    regularization_requested = 1,
                    regularization_status = 'pending'
                WHERE id = ?
            ''', (attendance_id,))
            
            db.commit()
            
            return {
                'success': True,
                'request_id': request_id,
                'message': 'Regularization request submitted successfully'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def process_regularization_request(self, request_id: int, admin_id: int,
                                     decision: str, admin_reason: str = None) -> Dict:
        """Process attendance regularization request"""
        try:
            db = get_db()

            # Get request details
            request = db.execute('''
                SELECT * FROM attendance_regularization_requests WHERE id = ?
            ''', (request_id,)).fetchone()

            if not request:
                return {'success': False, 'error': 'Request not found'}

            status = 'approved' if decision == 'approve' else 'rejected'
            processed_at = datetime.now()

            # Update request status
            db.execute('''
                UPDATE attendance_regularization_requests SET
                    status = ?, processed_by = ?, processed_at = ?, admin_reason = ?
                WHERE id = ?
            ''', (status, admin_id, processed_at, admin_reason, request_id))

            # Update attendance record
            if status == 'approved':
                # Apply the regularization
                if request['request_type'] == 'late_arrival':
                    db.execute('''
                        UPDATE attendance SET
                            time_in = ?, late_duration_minutes = 0,
                            regularization_status = 'approved'
                        WHERE id = ?
                    ''', (request['expected_time'], request['attendance_id']))
                elif request['request_type'] == 'early_departure':
                    db.execute('''
                        UPDATE attendance SET
                            time_out = ?, early_departure_minutes = 0,
                            regularization_status = 'approved'
                        WHERE id = ?
                    ''', (request['expected_time'], request['attendance_id']))
            else:
                # Mark as rejected
                db.execute('''
                    UPDATE attendance SET regularization_status = 'rejected'
                    WHERE id = ?
                ''', (request['attendance_id'],))

            db.commit()

            return {
                'success': True,
                'message': f'Regularization request {status} successfully'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_leave_integration_data(self, staff_id: int, date: str) -> Dict:
        """Check if staff has approved leave for the given date"""
        db = get_db()

        leave = db.execute('''
            SELECT * FROM leave_applications
            WHERE staff_id = ? AND status = 'approved'
            AND ? BETWEEN start_date AND end_date
        ''', (staff_id, date)).fetchone()

        if leave:
            return {
                'has_leave': True,
                'leave_type': leave['leave_type'],
                'reason': leave['reason'],
                'start_date': leave['start_date'],
                'end_date': leave['end_date']
            }

        return {'has_leave': False}

    def auto_mark_leave_attendance(self, school_id: int, date: str) -> Dict:
        """Automatically mark attendance for staff on approved leave"""
        try:
            db = get_db()

            # Get staff with approved leave for the date
            staff_on_leave = db.execute('''
                SELECT DISTINCT l.staff_id, l.leave_type, s.full_name
                FROM leave_applications l
                JOIN staff s ON l.staff_id = s.id
                WHERE l.school_id = ? AND l.status = 'approved'
                AND ? BETWEEN l.start_date AND l.end_date
            ''', (school_id, date)).fetchall()

            marked_count = 0

            for staff in staff_on_leave:
                # Check if attendance already exists
                existing = db.execute('''
                    SELECT id FROM attendance
                    WHERE staff_id = ? AND date = ?
                ''', (staff['staff_id'], date)).fetchone()

                if not existing:
                    # Mark as on leave
                    db.execute('''
                        INSERT INTO attendance (staff_id, school_id, date, status, notes)
                        VALUES (?, ?, ?, 'leave', ?)
                    ''', (staff['staff_id'], school_id, date, f"On {staff['leave_type']} leave"))
                    marked_count += 1

            db.commit()

            return {
                'success': True,
                'marked_count': marked_count,
                'message': f'Automatically marked {marked_count} staff members on leave'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}
