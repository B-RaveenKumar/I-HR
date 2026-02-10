"""
Advanced Timetable Management System
Handles period configuration, staff assignments, alterations, and admin overrides
"""

from datetime import datetime, time
import json
from database import get_db
import logging

logger = logging.getLogger(__name__)

class TimetableManager:
    """Core timetable management operations"""
    
    @staticmethod
    def enable_timetable_for_school(school_id, is_enabled=True):
        """Toggle timetable system for a school (Company Admin)"""
        db = get_db()
        try:
            db.execute('''
                INSERT INTO timetable_settings (school_id, is_enabled)
                VALUES (?, ?)
                ON CONFLICT(school_id) DO UPDATE SET is_enabled = excluded.is_enabled
            ''', (school_id, is_enabled))
            db.commit()
            return {'success': True, 'message': f'Timetable {"enabled" if is_enabled else "disabled"}'}
        except Exception as e:
            logger.error(f"Error toggling timetable: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_timetable_status(school_id):
        """Get timetable system status for school"""
        db = get_db()
        settings = db.execute(
            'SELECT * FROM timetable_settings WHERE school_id = ?',
            (school_id,)
        ).fetchone()
        
        if settings:
            return {
                'is_enabled': settings['is_enabled'],
                'number_of_periods': settings['number_of_periods'],
                'master_schedule': json.loads(settings['master_schedule']) if settings['master_schedule'] else {}
            }
        
        return {'is_enabled': False, 'number_of_periods': 8, 'master_schedule': {}}
    
    @staticmethod
    def create_period(school_id, period_number, period_name, start_time, end_time):
        """Create/update a period definition (School Admin)"""
        db = get_db()
        try:
            # Calculate duration
            start = datetime.strptime(start_time, '%H:%M')
            end = datetime.strptime(end_time, '%H:%M')
            duration = int((end - start).total_seconds() / 60)
            
            db.execute('''
                INSERT INTO timetable_periods 
                (school_id, period_number, period_name, start_time, end_time, duration_minutes)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(school_id, period_number) 
                DO UPDATE SET 
                    period_name = excluded.period_name,
                    start_time = excluded.start_time,
                    end_time = excluded.end_time,
                    duration_minutes = excluded.duration_minutes,
                    updated_at = CURRENT_TIMESTAMP
            ''', (school_id, period_number, period_name, start_time, end_time, duration))
            db.commit()
            return {'success': True, 'period_id': period_number}
        except Exception as e:
            logger.error(f"Error creating period: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_periods(school_id):
        """Get all periods for a school"""
        db = get_db()
        periods = db.execute(
            'SELECT * FROM timetable_periods WHERE school_id = ? ORDER BY period_number',
            (school_id,)
        ).fetchall()
        
        return [dict(p) for p in periods] if periods else []
    
    @staticmethod
    def delete_period(school_id, period_number):
        """Delete a period"""
        db = get_db()
        try:
            db.execute(
                'DELETE FROM timetable_periods WHERE school_id = ? AND period_number = ?',
                (school_id, period_number)
            )
            db.commit()
            return {'success': True}
        except Exception as e:
            logger.error(f"Error deleting period: {e}")
            return {'success': False, 'error': str(e)}


class DepartmentPermissionManager:
    """Manage department-level alteration permissions"""
    
    @staticmethod
    def set_department_permission(school_id, department, allow_alterations=True, allow_inbound=True):
        """Set alteration permissions for a department"""
        db = get_db()
        try:
            db.execute('''
                INSERT INTO timetable_department_permissions 
                (school_id, department, allow_alterations, allow_inbound)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(school_id, department)
                DO UPDATE SET 
                    allow_alterations = excluded.allow_alterations,
                    allow_inbound = excluded.allow_inbound,
                    updated_at = CURRENT_TIMESTAMP
            ''', (school_id, department, allow_alterations, allow_inbound))
            db.commit()
            return {'success': True}
        except Exception as e:
            logger.error(f"Error setting department permission: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_department_permissions(school_id):
        """Get all department permissions"""
        db = get_db()
        perms = db.execute(
            'SELECT * FROM timetable_department_permissions WHERE school_id = ?',
            (school_id,)
        ).fetchall()
        
        return [dict(p) for p in perms] if perms else []
    
    @staticmethod
    def can_department_send_request(school_id, department):
        """Check if department can send swap requests"""
        db = get_db()
        perm = db.execute(
            'SELECT allow_alterations FROM timetable_department_permissions WHERE school_id = ? AND department = ?',
            (school_id, department)
        ).fetchone()
        
        return perm['allow_alterations'] if perm else True  # Default: allow
    
    @staticmethod
    def can_department_receive_request(school_id, department):
        """Check if other staff can target this department"""
        db = get_db()
        perm = db.execute(
            'SELECT allow_inbound FROM timetable_department_permissions WHERE school_id = ? AND department = ?',
            (school_id, department)
        ).fetchone()
        
        return perm['allow_inbound'] if perm else True  # Default: allow


class TimetableAssignmentManager:
    """Manage staff timetable assignments and alterations"""
    
    @staticmethod
    def assign_staff_to_period(school_id, staff_id, day_of_week, period_number, class_subject=''):
        """Assign staff to a period"""
        db = get_db()
        try:
            db.execute('''
                INSERT INTO timetable_assignments 
                (school_id, staff_id, day_of_week, period_number, class_subject, is_assigned)
                VALUES (?, ?, ?, ?, ?, 1)
                ON CONFLICT(school_id, staff_id, day_of_week, period_number)
                DO UPDATE SET 
                    class_subject = excluded.class_subject,
                    is_assigned = 1,
                    updated_at = CURRENT_TIMESTAMP
            ''', (school_id, staff_id, day_of_week, period_number, class_subject))
            db.commit()
            return {'success': True}
        except Exception as e:
            logger.error(f"Error assigning staff: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_staff_timetable(school_id, staff_id):
        """Get complete timetable for a staff member"""
        db = get_db()
        assignments = db.execute('''
            SELECT ta.*, tp.start_time, tp.end_time, tp.period_name
            FROM timetable_assignments ta
            LEFT JOIN timetable_periods tp ON ta.school_id = tp.school_id AND ta.period_number = tp.period_number
            WHERE ta.school_id = ? AND ta.staff_id = ?
            ORDER BY ta.day_of_week, ta.period_number
        ''', (school_id, staff_id)).fetchall()
        
        return [dict(a) for a in assignments] if assignments else []
    
    @staticmethod
    def get_daily_timetable(school_id, day_of_week):
        """Get timetable for entire school on a specific day"""
        db = get_db()
        assignments = db.execute('''
            SELECT ta.*, s.full_name, s.department, tp.start_time, tp.end_time, tp.period_name
            FROM timetable_assignments ta
            JOIN staff s ON ta.staff_id = s.id
            LEFT JOIN timetable_periods tp ON ta.school_id = tp.school_id AND ta.period_number = tp.period_number
            WHERE ta.school_id = ? AND ta.day_of_week = ? AND ta.is_assigned = 1
            ORDER BY ta.period_number, s.full_name
        ''', (school_id, day_of_week)).fetchall()
        
        return [dict(a) for a in assignments] if assignments else []
    
    @staticmethod
    def lock_assignment(school_id, assignment_id, locked_by_admin_id, reason=''):
        """Admin locks a staff assignment"""
        db = get_db()
        try:
            db.execute('''
                UPDATE timetable_assignments
                SET is_locked = 1, locked_by = ?, locked_reason = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND school_id = ?
            ''', (locked_by_admin_id, reason, assignment_id, school_id))
            db.commit()
            return {'success': True}
        except Exception as e:
            logger.error(f"Error locking assignment: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def admin_override_assignment(school_id, assignment_id, new_staff_id, admin_id, notes=''):
        """Admin reassigns a slot instantly (override)"""
        db = get_db()
        try:
            # Get current assignment details
            assignment = db.execute(
                'SELECT * FROM timetable_assignments WHERE id = ? AND school_id = ?',
                (assignment_id, school_id)
            ).fetchone()
            
            if not assignment:
                return {'success': False, 'error': 'Assignment not found'}
            
            # Update with new staff
            db.execute('''
                UPDATE timetable_assignments
                SET staff_id = ?, is_locked = 1, locked_reason = 'Admin Override', 
                    locked_by = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND school_id = ?
            ''', (new_staff_id, admin_id, assignment_id, school_id))
            
            # Log the override
            db.execute('''
                INSERT INTO timetable_alteration_requests 
                (school_id, assignment_id, requester_staff_id, target_staff_id, 
                 alteration_type, status, admin_notes, processed_by, processed_at)
                VALUES (?, ?, ?, ?, 'admin_override', 'admin_override', ?, ?, CURRENT_TIMESTAMP)
            ''', (school_id, assignment_id, assignment['staff_id'], new_staff_id, notes, admin_id))
            
            db.commit()
            return {'success': True, 'message': 'Assignment reassigned successfully'}
        except Exception as e:
            logger.error(f"Error in admin override: {e}")
            return {'success': False, 'error': str(e)}


class AlterationManager:
    """Manage swap requests and alterations"""
    
    @staticmethod
    def request_peer_swap(school_id, requester_staff_id, assignment_id, target_staff_id, reason=''):
        """Staff requests to swap with another staff member"""
        db = get_db()
        try:
            # Validate target staff is available and department allows inbound
            assignment = db.execute(
                'SELECT * FROM timetable_assignments WHERE id = ? AND school_id = ?',
                (assignment_id, school_id)
            ).fetchone()
            
            if not assignment:
                return {'success': False, 'error': 'Assignment not found'}
            
            requester_dept = db.execute(
                'SELECT department FROM staff WHERE id = ? AND school_id = ?',
                (requester_staff_id, school_id)
            ).fetchone()
            
            target_dept = db.execute(
                'SELECT department FROM staff WHERE id = ? AND school_id = ?',
                (target_staff_id, school_id)
            ).fetchone()
            
            # Check if target department allows inbound requests
            if not DepartmentPermissionManager.can_department_receive_request(school_id, target_dept['department']):
                return {'success': False, 'error': 'Target department does not allow swap requests'}
            
            # Check if requester's department allows sending requests
            if not DepartmentPermissionManager.can_department_send_request(school_id, requester_dept['department']):
                return {'success': False, 'error': 'Your department is restricted from sending swap requests'}
            
            # Create request
            db.execute('''
                INSERT INTO timetable_alteration_requests 
                (school_id, assignment_id, requester_staff_id, target_staff_id, 
                 alteration_type, reason)
                VALUES (?, ?, ?, ?, 'peer_swap', ?)
            ''', (school_id, assignment_id, requester_staff_id, target_staff_id, reason))
            
            db.commit()
            return {'success': True, 'message': 'Swap request sent successfully'}
        except Exception as e:
            logger.error(f"Error requesting swap: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def respond_to_swap_request(request_id, staff_id, acceptance, response_reason=''):
        """Target staff accepts or rejects swap request"""
        db = get_db()
        try:
            request_data = db.execute(
                'SELECT * FROM timetable_alteration_requests WHERE id = ?',
                (request_id,)
            ).fetchone()
            
            if not request_data:
                return {'success': False, 'error': 'Request not found'}
            
            if request_data['target_staff_id'] != staff_id:
                return {'success': False, 'error': 'Unauthorized'}
            
            status = 'accepted' if acceptance else 'rejected'
            
            db.execute('''
                UPDATE timetable_alteration_requests
                SET status = ?, response_reason = ?, responded_by = ?, responded_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, response_reason, staff_id, request_id))
            
            # If accepted, swap the assignments
            if acceptance:
                assignment = db.execute(
                    'SELECT * FROM timetable_alteration_requests WHERE id = ?',
                    (request_id,)
                ).fetchone()
                
                # Swap staff assignments
                requester_assignment = db.execute(
                    'SELECT * FROM timetable_assignments WHERE id = ?',
                    (assignment['assignment_id'],)
                ).fetchone()
                
                db.execute('''
                    UPDATE timetable_assignments SET staff_id = ?
                    WHERE id = ?
                ''', (staff_id, assignment['assignment_id']))
                
                db.commit()
            
            return {'success': True, 'message': f'Request {status}'}
        except Exception as e:
            logger.error(f"Error responding to swap: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_pending_requests(school_id, staff_id=None, filter_type='received'):
        """Get pending swap requests (filter_type: 'received', 'sent', 'all')"""
        db = get_db()
        
        if filter_type == 'received':
            requests = db.execute('''
                SELECT tar.*, s1.full_name as requester_name, s1.department as requester_dept,
                       s2.full_name as target_name, s2.department as target_dept,
                       tp.period_name, tp.start_time, tp.end_time
                FROM timetable_alteration_requests tar
                JOIN staff s1 ON tar.requester_staff_id = s1.id
                JOIN staff s2 ON tar.target_staff_id = s2.id
                LEFT JOIN timetable_periods tp ON tar.school_id = tp.school_id 
                    AND (SELECT period_number FROM timetable_assignments WHERE id = tar.assignment_id) = tp.period_number
                WHERE tar.school_id = ? AND tar.target_staff_id = ? AND tar.status = 'pending'
                ORDER BY tar.created_at DESC
            ''', (school_id, staff_id)).fetchall()
        
        elif filter_type == 'sent':
            requests = db.execute('''
                SELECT tar.*, s1.full_name as requester_name, s1.department as requester_dept,
                       s2.full_name as target_name, s2.department as target_dept,
                       tp.period_name, tp.start_time, tp.end_time
                FROM timetable_alteration_requests tar
                JOIN staff s1 ON tar.requester_staff_id = s1.id
                JOIN staff s2 ON tar.target_staff_id = s2.id
                LEFT JOIN timetable_periods tp ON tar.school_id = tp.school_id 
                    AND (SELECT period_number FROM timetable_assignments WHERE id = tar.assignment_id) = tp.period_number
                WHERE tar.school_id = ? AND tar.requester_staff_id = ? AND tar.status = 'pending'
                ORDER BY tar.created_at DESC
            ''', (school_id, staff_id)).fetchall()
        
        else:  # all
            requests = db.execute('''
                SELECT tar.*, s1.full_name as requester_name, s1.department as requester_dept,
                       s2.full_name as target_name, s2.department as target_dept,
                       tp.period_name, tp.start_time, tp.end_time
                FROM timetable_alteration_requests tar
                JOIN staff s1 ON tar.requester_staff_id = s1.id
                JOIN staff s2 ON tar.target_staff_id = s2.id
                LEFT JOIN timetable_periods tp ON tar.school_id = tp.school_id 
                    AND (SELECT period_number FROM timetable_assignments WHERE id = tar.assignment_id) = tp.period_number
                WHERE tar.school_id = ? AND tar.status = 'pending'
                ORDER BY tar.created_at DESC
            ''', (school_id,)).fetchall()
        
        return [dict(r) for r in requests] if requests else []


class SelfAllocationManager:
    """Manage staff self-allocation (filling empty slots)"""
    
    @staticmethod
    def allocate_to_empty_slot(school_id, staff_id, day_of_week, period_number, class_subject):
        """Staff fills an empty slot (self-allocation)"""
        db = get_db()
        try:
            # Check if slot is truly empty
            existing = db.execute('''
                SELECT * FROM timetable_assignments 
                WHERE school_id = ? AND day_of_week = ? AND period_number = ?
                AND is_assigned = 1
            ''', (school_id, day_of_week, period_number)).fetchone()
            
            if existing:
                return {'success': False, 'error': 'Slot is already assigned'}
            
            # Create self-allocation (automatically locked to staff)
            db.execute('''
                INSERT INTO timetable_self_allocations 
                (school_id, staff_id, day_of_week, period_number, class_subject, is_admin_locked)
                VALUES (?, ?, ?, ?, ?, 1)
                ON CONFLICT(school_id, staff_id, day_of_week, period_number)
                DO UPDATE SET is_admin_locked = 1, updated_at = CURRENT_TIMESTAMP
            ''', (school_id, staff_id, day_of_week, period_number, class_subject))
            
            db.commit()
            return {'success': True, 'message': 'Slot allocated successfully'}
        except Exception as e:
            logger.error(f"Error in self-allocation: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_staff_allocations(school_id, staff_id):
        """Get self-allocated slots for staff"""
        db = get_db()
        allocations = db.execute('''
            SELECT tsa.*, tp.period_name, tp.start_time, tp.end_time
            FROM timetable_self_allocations tsa
            LEFT JOIN timetable_periods tp ON tsa.school_id = tp.school_id AND tsa.period_number = tp.period_number
            WHERE tsa.school_id = ? AND tsa.staff_id = ?
            ORDER BY tsa.day_of_week, tsa.period_number
        ''', (school_id, staff_id)).fetchall()
        
        return [dict(a) for a in allocations] if allocations else []
    
    @staticmethod
    def update_allocation(school_id, allocation_id, class_subject, locked_by_admin=False):
        """Update self-allocation (staff can edit, admin can lock)"""
        db = get_db()
        try:
            db.execute('''
                UPDATE timetable_self_allocations
                SET class_subject = ?, is_admin_locked = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND school_id = ?
            ''', (class_subject, locked_by_admin, allocation_id, school_id))
            db.commit()
            return {'success': True}
        except Exception as e:
            logger.error(f"Error updating allocation: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def delete_allocation(school_id, allocation_id, staff_id):
        """Delete self-allocation (staff can only delete unlocked)"""
        db = get_db()
        try:
            allocation = db.execute(
                'SELECT * FROM timetable_self_allocations WHERE id = ? AND school_id = ?',
                (allocation_id, school_id)
            ).fetchone()
            
            if not allocation:
                return {'success': False, 'error': 'Allocation not found'}
            
            if allocation['is_admin_locked'] and allocation['staff_id'] != staff_id:
                return {'success': False, 'error': 'Cannot delete admin-locked allocation'}
            
            db.execute(
                'DELETE FROM timetable_self_allocations WHERE id = ? AND school_id = ?',
                (allocation_id, school_id)
            )
            db.commit()
            return {'success': True}
        except Exception as e:
            logger.error(f"Error deleting allocation: {e}")
            return {'success': False, 'error': str(e)}
