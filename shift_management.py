# shift_management.py
"""
Enhanced Shift and Attendance Management System

This module handles the core logic for:
- Shift type definitions and calculations
- Grace period handling
- Late arrival and early departure detection
- Attendance status determination
"""

import datetime
from typing import Dict, Tuple, Optional
from database import get_db


class ShiftManager:
    """Manages shift definitions and attendance calculations"""
    
    def __init__(self):
        self.shift_definitions = self._load_shift_definitions()
    
    def _load_shift_definitions(self) -> Dict:
        """Load shift definitions from database"""
        db = get_db()
        
        # Always prioritize institution timings for 'general' shift
        shift_dict = {}

        # First, ensure 'general' shift uses current institution timings
        try:
            from database import get_institution_timings
            timings = get_institution_timings()

            shift_dict['general'] = {
                'start_time': timings['checkin_time'],
                'end_time': timings['checkout_time'],
                'grace_period_minutes': 0,  # Strict timing
                'description': f"Institution Shift ({'Custom' if timings['is_custom'] else 'Default'})"
            }

            print(f"✅ General shift synchronized with institution timings: {timings['checkin_time']} - {timings['checkout_time']}")

        except Exception as e:
            print(f"Could not load institution timings: {e}")
            # Fallback for general shift
            shift_dict['general'] = {
                'start_time': datetime.time(9, 0),
                'end_time': datetime.time(17, 0),
                'grace_period_minutes': 0,
                'description': 'Default Hardcoded Shift (Strict timing)'
            }

        # Then try to load additional shifts from shift_definitions table
        try:
            shifts = db.execute('''
                SELECT shift_type, start_time, end_time, grace_period_minutes, description
                FROM shift_definitions
                WHERE is_active = 1 AND shift_type != 'general'
            ''').fetchall()

            for shift in shifts:
                shift_dict[shift['shift_type']] = {
                    'start_time': datetime.datetime.strptime(shift['start_time'], '%H:%M:%S').time(),
                    'end_time': datetime.datetime.strptime(shift['end_time'], '%H:%M:%S').time(),
                    'grace_period_minutes': shift['grace_period_minutes'],
                    'description': shift['description']
                }

            if len(shifts) > 0:
                print(f"✅ Loaded {len(shifts)} additional shifts from database")

        except Exception as e:
            print(f"Could not load additional shift definitions: {e}")

        return shift_dict
    
    def reload_shift_definitions(self):
        """Reload shift definitions - useful when institution timings change"""
        print("🔄 Reloading shift definitions from institution timings...")
        self.shift_definitions = self._load_shift_definitions()
        print("✅ Shift definitions reloaded with latest institution timings")

    def sync_with_institution_timings(self):
        """Synchronize general shift with current institution timings"""
        try:
            from database import get_institution_timings
            timings = get_institution_timings()

            # Update the general shift in memory
            self.shift_definitions['general'] = {
                'start_time': timings['checkin_time'],
                'end_time': timings['checkout_time'],
                'grace_period_minutes': 0,  # Strict timing
                'description': f"Institution Shift ({'Custom' if timings['is_custom'] else 'Default'})"
            }

            print(f"✅ General shift synchronized with institution timings: {timings['checkin_time']} - {timings['checkout_time']}")
            return True

        except Exception as e:
            print(f"❌ Failed to sync with institution timings: {e}")
            return False
    
    def get_shift_info(self, shift_type: str) -> Optional[Dict]:
        """Get shift information for a given shift type"""
        return self.shift_definitions.get(shift_type)
    
    def calculate_attendance_status(self, shift_type: str, check_in_time: datetime.time, 
                                  check_out_time: Optional[datetime.time] = None) -> Dict:
        """
        Calculate attendance status based on shift type and times
        
        Returns:
        {
            'status': 'present'|'late'|'left_soon',
            'late_duration_minutes': int,
            'early_departure_minutes': int,
            'requires_regularization': bool,
            'shift_start_time': time,
            'shift_end_time': time
        }
        """
        shift_info = self.get_shift_info(shift_type)
        if not shift_info:
            # Default to general shift if not found
            shift_info = self.get_shift_info('general')
        
        if not shift_info:
            raise ValueError(f"Shift type '{shift_type}' not found and no default general shift available")
        
        start_time = shift_info['start_time']
        end_time = shift_info['end_time']
        # Note: grace_period is ignored for strict timing rules

        result = {
            'status': 'present',
            'late_duration_minutes': 0,
            'early_departure_minutes': 0,
            'requires_regularization': False,
            'shift_start_time': start_time,
            'shift_end_time': end_time
        }
        
        # STRICT TIMING: Check for late arrival (any time after start_time is late)
        if check_in_time > start_time:
            result['status'] = 'late'
            # Calculate late duration from shift start time (not grace cutoff)
            check_in_dt = datetime.datetime.combine(datetime.date.today(), check_in_time)
            start_dt = datetime.datetime.combine(datetime.date.today(), start_time)
            late_duration = check_in_dt - start_dt
            result['late_duration_minutes'] = int(late_duration.total_seconds() / 60)
            result['requires_regularization'] = True

            print(f"🔍 SHIFT DEBUG: {check_in_time} > {start_time} = LATE ({result['late_duration_minutes']} min)")
        else:
            print(f"🔍 SHIFT DEBUG: {check_in_time} <= {start_time} = PRESENT")

        # Check for early departure (if check_out_time is provided)
        if check_out_time and check_out_time < end_time:
            if result['status'] == 'late':
                # If already late, don't change status but note early departure
                pass
            else:
                result['status'] = 'left_soon'

            # Calculate early departure duration in minutes
            check_out_dt = datetime.datetime.combine(datetime.date.today(), check_out_time)
            end_time_dt = datetime.datetime.combine(datetime.date.today(), end_time)
            early_duration = end_time_dt - check_out_dt
            result['early_departure_minutes'] = int(early_duration.total_seconds() / 60)
            result['requires_regularization'] = True
        
        return result
    
    def format_duration_text(self, minutes: int, duration_type: str = 'late') -> str:
        """Format duration in minutes to human-readable text"""
        if minutes <= 0:
            return ""
        
        hours = minutes // 60
        mins = minutes % 60
        
        if hours > 0:
            if mins > 0:
                duration_str = f"{hours} hour{'s' if hours > 1 else ''} {mins} minute{'s' if mins > 1 else ''}"
            else:
                duration_str = f"{hours} hour{'s' if hours > 1 else ''}"
        else:
            duration_str = f"{mins} minute{'s' if mins > 1 else ''}"
        
        if duration_type == 'late':
            return f"Late by {duration_str}"
        elif duration_type == 'early':
            return f"Left {duration_str} soon"
        else:
            return duration_str
    
    def get_all_shift_types(self) -> Dict:
        """Get all available shift types"""
        return self.shift_definitions
    
    def refresh_shift_definitions(self):
        """Refresh shift definitions from database"""
        self.shift_definitions = self._load_shift_definitions()


class AttendanceRegularizationManager:
    """Manages attendance regularization requests"""
    
    @staticmethod
    def create_regularization_request(attendance_id: int, staff_id: int, school_id: int,
                                    request_type: str, original_time: datetime.time,
                                    expected_time: datetime.time, duration_minutes: int,
                                    staff_reason: str = None) -> int:
        """
        Create a new regularization request
        
        Args:
            attendance_id: ID of the attendance record
            staff_id: ID of the staff member
            school_id: ID of the school
            request_type: 'late_arrival' or 'early_departure'
            original_time: Actual check-in/check-out time
            expected_time: Expected check-in/check-out time
            duration_minutes: Duration of lateness/early departure
            staff_reason: Optional reason provided by staff
        
        Returns:
            ID of the created request
        """
        db = get_db()
        
        cursor = db.execute('''
            INSERT INTO attendance_regularization_requests 
            (attendance_id, staff_id, school_id, request_type, original_time, 
             expected_time, duration_minutes, staff_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (attendance_id, staff_id, school_id, request_type, 
              original_time.strftime('%H:%M:%S'), expected_time.strftime('%H:%M:%S'),
              duration_minutes, staff_reason))
        
        request_id = cursor.lastrowid
        
        # Update attendance record to mark regularization as requested
        db.execute('''
            UPDATE attendance 
            SET regularization_requested = 1, regularization_status = 'pending'
            WHERE id = ?
        ''', (attendance_id,))
        
        db.commit()
        return request_id
    
    @staticmethod
    def get_pending_requests(school_id: int) -> list:
        """Get all pending regularization requests for a school"""
        db = get_db()
        
        requests = db.execute('''
            SELECT r.*, s.full_name, s.staff_id as staff_number, a.date, a.time_in, a.time_out
            FROM attendance_regularization_requests r
            JOIN staff s ON r.staff_id = s.id
            JOIN attendance a ON r.attendance_id = a.id
            WHERE r.school_id = ? AND r.status = 'pending'
            ORDER BY r.requested_at DESC
        ''', (school_id,)).fetchall()
        
        return [dict(req) for req in requests]
    
    @staticmethod
    def process_request(request_id: int, admin_id: int, decision: str, admin_reason: str = None) -> bool:
        """
        Process a regularization request (approve or reject)
        
        Args:
            request_id: ID of the request
            admin_id: ID of the admin processing the request
            decision: 'approved' or 'rejected'
            admin_reason: Optional reason for rejection
        
        Returns:
            True if successful, False otherwise
        """
        if decision not in ['approved', 'rejected']:
            return False
        
        db = get_db()
        
        try:
            # Update the request
            db.execute('''
                UPDATE attendance_regularization_requests
                SET status = ?, processed_by = ?, processed_at = ?, admin_reason = ?
                WHERE id = ?
            ''', (decision, admin_id, datetime.datetime.now(), admin_reason, request_id))
            
            # Get request details for updating attendance
            request_info = db.execute('''
                SELECT attendance_id, staff_id, school_id, request_type
                FROM attendance_regularization_requests
                WHERE id = ?
            ''', (request_id,)).fetchone()
            
            if request_info:
                # Update attendance record
                db.execute('''
                    UPDATE attendance
                    SET regularization_status = ?
                    WHERE id = ?
                ''', (decision, request_info['attendance_id']))
                
                # Create notification for staff
                NotificationManager.create_notification(
                    staff_id=request_info['staff_id'],
                    school_id=request_info['school_id'],
                    title=f"Regularization Request {decision.title()}",
                    message=f"Your {request_info['request_type'].replace('_', ' ')} regularization request has been {decision}.",
                    notification_type=f"regularization_{decision}",
                    related_request_id=request_id
                )
            
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            print(f"Error processing regularization request: {e}")
            return False


class NotificationManager:
    """Manages employee notifications"""
    
    @staticmethod
    def create_notification(staff_id: int, school_id: int, title: str, message: str,
                          notification_type: str = 'general', related_request_id: int = None) -> int:
        """Create a new notification for a staff member"""
        db = get_db()
        
        cursor = db.execute('''
            INSERT INTO notifications (staff_id, school_id, title, message, notification_type, related_request_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (staff_id, school_id, title, message, notification_type, related_request_id))
        
        notification_id = cursor.lastrowid
        db.commit()
        return notification_id
    
    @staticmethod
    def get_staff_notifications(staff_id: int, unread_only: bool = False) -> list:
        """Get notifications for a staff member"""
        db = get_db()
        
        query = '''
            SELECT * FROM notifications
            WHERE staff_id = ?
        '''
        params = [staff_id]
        
        if unread_only:
            query += ' AND is_read = 0'
        
        query += ' ORDER BY created_at DESC'
        
        notifications = db.execute(query, params).fetchall()
        return [dict(notif) for notif in notifications]
    
    @staticmethod
    def mark_notification_read(notification_id: int) -> bool:
        """Mark a notification as read"""
        db = get_db()
        
        try:
            db.execute('UPDATE notifications SET is_read = 1 WHERE id = ?', (notification_id,))
            db.commit()
            return True
        except:
            return False
