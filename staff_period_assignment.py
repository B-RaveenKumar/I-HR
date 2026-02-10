"""
Staff Period Assignment Module
Handles individual staff member period assignments with validation and conflict checking
"""

import sqlite3
from datetime import datetime, date
from database import get_db


class StaffPeriodAssignment:
    """Class to manage individual staff period assignments"""

    def __init__(self, school_id=None):
        """Initialize with school context"""
        self.school_id = school_id

    def assign_period_to_staff(self, staff_id, day_of_week, period_number, school_id=None):
        """
        Assign a specific period to a staff member

        Args:
            staff_id (int): ID of the staff member
            day_of_week (int): Day index (0=Sunday, 6=Saturday)
            period_number (int): Period number to assign
            school_id (int): School ID (optional, uses self.school_id if not provided)

        Returns:
            dict: {
                'success': bool,
                'message': str,
                'assignment_id': int (if successful),
                'data': dict (if successful)
            }
        """
        school_id = school_id or self.school_id
        if not school_id:
            return {'success': False, 'error': 'School ID is required'}

        db = get_db()
        
        try:
            # Verify staff exists and is from the same school
            staff = db.execute('''
                SELECT id, full_name FROM staff 
                WHERE id = ? AND school_id = ?
            ''', (staff_id, school_id)).fetchone()

            if not staff:
                return {'success': False, 'error': 'Staff member not found'}

            # Verify period exists
            period = db.execute('''
                SELECT period_number, start_time, end_time FROM timetable_periods
                WHERE school_id = ? AND period_number = ?
            ''', (school_id, period_number)).fetchone()

            if not period:
                return {'success': False, 'error': f'Period {period_number} not found'}

            # Check for duplicate assignment (same staff, day, and period)
            existing = db.execute('''
                SELECT id FROM timetable_assignments
                WHERE school_id = ? AND staff_id = ? AND day_of_week = ? AND period_number = ?
            ''', (school_id, staff_id, day_of_week, period_number)).fetchone()

            if existing:
                return {
                    'success': False,
                    'error': f'Staff {staff[1]} is already assigned to this period on this day'
                }

            # Check for staff conflicts (staff can't teach 2 classes at same time)
            conflict = db.execute('''
                SELECT ta.id, s.full_name as section_name FROM timetable_assignments ta
                JOIN timetable_sections s ON ta.section_id = s.id
                WHERE ta.school_id = ? AND ta.staff_id = ? 
                    AND ta.day_of_week = ? AND ta.period_number = ?
            ''', (school_id, staff_id, day_of_week, period_number)).fetchone()

            if conflict:
                return {
                    'success': False,
                    'error': f'Staff {staff[1]} is already assigned to {conflict[1]} during this period'
                }

            # Create the assignment
            cursor = db.execute('''
                INSERT INTO timetable_assignments 
                (school_id, staff_id, day_of_week, period_number, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                school_id,
                staff_id,
                day_of_week,
                period_number,
                datetime.now(),
                datetime.now()
            ))
            db.commit()

            assignment_id = cursor.lastrowid
            
            return {
                'success': True,
                'message': f'✅ Period {period_number} assigned to {staff[1]} on day {day_of_week}',
                'assignment_id': assignment_id,
                'data': {
                    'staff_id': staff_id,
                    'staff_name': staff[1],
                    'day_of_week': day_of_week,
                    'period_number': period_number
                }
            }

        except Exception as e:
            return {'success': False, 'error': f'Database error: {str(e)}'}

    def get_staff_assigned_periods(self, staff_id, school_id=None):
        """
        Get all periods assigned to a staff member

        Args:
            staff_id (int): ID of the staff member
            school_id (int): School ID (optional)

        Returns:
            dict: {
                'success': bool,
                'staff_name': str,
                'staff_id': int,
                'periods': [list of period dictionaries],
                'total_periods': int
            }
        """
        school_id = school_id or self.school_id
        if not school_id:
            return {'success': False, 'error': 'School ID is required'}

        db = get_db()

        try:
            # Get staff member
            staff = db.execute('''
                SELECT id, full_name FROM staff
                WHERE id = ? AND school_id = ?
            ''', (staff_id, school_id)).fetchone()

            if not staff:
                return {'success': False, 'error': 'Staff member not found'}

            # Get all assigned periods
            periods = db.execute('''
                SELECT 
                    ta.id as assignment_id,
                    ta.period_number,
                    ta.day_of_week,
                    tp.start_time,
                    tp.end_time,
                    ta.created_at
                FROM timetable_assignments ta
                JOIN timetable_periods tp ON ta.period_number = tp.period_number 
                    AND ta.school_id = tp.school_id
                WHERE ta.school_id = ? AND ta.staff_id = ?
                ORDER BY ta.day_of_week, ta.period_number
            ''', (school_id, staff_id)).fetchall()

            days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            
            periods_list = [
                {
                    'assignment_id': p[0],
                    'period_number': p[1],
                    'day_of_week': p[2],
                    'day_name': days[p[2]],
                    'start_time': p[3],
                    'end_time': p[4],
                    'assigned_date': p[5]
                }
                for p in periods
            ]

            return {
                'success': True,
                'staff_id': staff_id,
                'staff_name': staff[1],
                'periods': periods_list,
                'total_periods': len(periods_list)
            }

        except Exception as e:
            return {'success': False, 'error': f'Database error: {str(e)}'}

    def remove_staff_period_assignment(self, assignment_id, school_id=None):
        """
        Remove a period assignment from a staff member

        Args:
            assignment_id (int): ID of the assignment to remove
            school_id (int): School ID (optional)

        Returns:
            dict: {'success': bool, 'message': str}
        """
        school_id = school_id or self.school_id
        if not school_id:
            return {'success': False, 'error': 'School ID is required'}

        db = get_db()

        try:
            # Get assignment details before deletion
            assignment = db.execute('''
                SELECT ta.id, ta.staff_id, s.full_name, ta.period_number, ta.day_of_week
                FROM timetable_assignments ta
                JOIN staff s ON ta.staff_id = s.id
                WHERE ta.id = ? AND ta.school_id = ?
            ''', (assignment_id, school_id)).fetchone()

            if not assignment:
                return {'success': False, 'error': 'Assignment not found'}

            # Delete the assignment
            db.execute('''
                DELETE FROM timetable_assignments
                WHERE id = ? AND school_id = ?
            ''', (assignment_id, school_id))
            db.commit()

            days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            day_name = days[assignment[4]]

            return {
                'success': True,
                'message': f'✅ Removed period {assignment[3]} assignment for {assignment[2]} on {day_name}',
                'data': {
                    'staff_id': assignment[1],
                    'staff_name': assignment[2],
                    'period_number': assignment[3],
                    'day_of_week': assignment[4]
                }
            }

        except Exception as e:
            return {'success': False, 'error': f'Database error: {str(e)}'}

    def check_staff_period_conflict(self, staff_id, day_of_week, period_number, 
                                   exclude_assignment_id=None, school_id=None):
        """
        Check if a staff member has a conflict for a given period

        Args:
            staff_id (int): Staff ID to check
            day_of_week (int): Day index (0-6)
            period_number (int): Period number
            exclude_assignment_id (int): Assignment ID to exclude from check (for updates)
            school_id (int): School ID (optional)

        Returns:
            dict: {
                'success': bool,
                'has_conflict': bool,
                'conflict_message': str (if conflict exists)
            }
        """
        school_id = school_id or self.school_id
        if not school_id:
            return {'success': False, 'error': 'School ID is required'}

        db = get_db()

        try:
            # Check for conflicts
            query = '''
                SELECT ta.id, ta.period_number, ta.day_of_week, s.full_name
                FROM timetable_assignments ta
                JOIN timetable_sections s ON ta.section_id = s.id
                WHERE ta.school_id = ? AND ta.staff_id = ? 
                    AND ta.day_of_week = ? AND ta.period_number = ?
            '''
            params = [school_id, staff_id, day_of_week, period_number]

            if exclude_assignment_id:
                query += ' AND ta.id != ?'
                params.append(exclude_assignment_id)

            conflict = db.execute(query, params).fetchone()

            if conflict:
                return {
                    'success': True,
                    'has_conflict': True,
                    'conflict_message': f'Staff already assigned to {conflict[3]} at period {conflict[1]}'
                }

            return {
                'success': True,
                'has_conflict': False,
                'conflict_message': None
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Database error: {str(e)}'
            }

    def get_staff_schedule_grid(self, staff_id, school_id=None):
        """
        Get a visual grid of staff member's schedule

        Args:
            staff_id (int): Staff ID
            school_id (int): School ID (optional)

        Returns:
            dict: {
                'success': bool,
                'staff_name': str,
                'grid': [[7 x 8 schedule grid]],
                'days': [...],
                'periods': [...]
            }
        """
        school_id = school_id or self.school_id
        if not school_id:
            return {'success': False, 'error': 'School ID is required'}

        db = get_db()

        try:
            # Get staff
            staff = db.execute('''
                SELECT id, full_name FROM staff
                WHERE id = ? AND school_id = ?
            ''', (staff_id, school_id)).fetchone()

            if not staff:
                return {'success': False, 'error': 'Staff not found'}

            # Get all periods
            periods = db.execute('''
                SELECT period_number, start_time, end_time
                FROM timetable_periods
                WHERE school_id = ?
                ORDER BY period_number
            ''', (school_id,)).fetchall()

            # Create 7x8 grid (7 days, 8 periods max)
            grid = [[''] * len(periods) for _ in range(7)]
            days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

            # Get staff assignments
            assignments = db.execute('''
                SELECT ta.day_of_week, ta.period_number, s.section_name
                FROM timetable_assignments ta
                LEFT JOIN timetable_sections s ON ta.section_id = s.id
                WHERE ta.school_id = ? AND ta.staff_id = ?
            ''', (school_id, staff_id)).fetchall()

            # Fill grid
            for day, period, section in assignments:
                for idx, p in enumerate(periods):
                    if p[0] == period:
                        grid[day][idx] = section or 'Assigned'
                        break

            return {
                'success': True,
                'staff_id': staff_id,
                'staff_name': staff[1],
                'grid': grid,
                'days': days,
                'periods': [
                    {
                        'period_number': p[0],
                        'start_time': p[1],
                        'end_time': p[2]
                    } for p in periods
                ]
            }

        except Exception as e:
            return {'success': False, 'error': f'Database error: {str(e)}'}
