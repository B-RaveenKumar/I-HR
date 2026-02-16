"""
Timetable API Routes
Handles all API endpoints for timetable management
"""

from flask import Blueprint, request, jsonify, session
from database import get_db
from functools import wraps
import sqlite3
from datetime import datetime

timetable_api = Blueprint('timetable_api', __name__)


def company_admin_required(f):
    """Decorator to ensure only company admins can access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_type') != 'company_admin':
            return jsonify({'success': False, 'error': 'Unauthorized access'}), 403
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to ensure only school admins can access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_type') != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized access'}), 403
        return f(*args, **kwargs)
    return decorated_function


# ==================== COMPANY ADMIN ENDPOINTS ====================

@timetable_api.route('/api/timetable/toggle-school', methods=['POST'])
@company_admin_required
def toggle_school_timetable():
    """
    Company Admin: Enable/Disable timetable module for a school
    """
    try:
        data = request.get_json()
        school_id = data.get('school_id')
        is_enabled = data.get('is_enabled', False)
        
        if not school_id:
            return jsonify({'success': False, 'error': 'School ID is required'}), 400
        
        db = get_db()
        cursor = db.cursor()
        
        # Check if timetable_settings exists for this school
        cursor.execute('''
            SELECT id FROM timetable_settings WHERE school_id = ?
        ''', (school_id,))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing setting
            cursor.execute('''
                UPDATE timetable_settings 
                SET is_enabled = ?, updated_at = CURRENT_TIMESTAMP
                WHERE school_id = ?
            ''', (is_enabled, school_id))
        else:
            # Create new setting
            cursor.execute('''
                INSERT INTO timetable_settings (school_id, is_enabled)
                VALUES (?, ?)
            ''', (school_id, is_enabled))
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': f'Timetable module {"enabled" if is_enabled else "disabled"} for school',
            'is_enabled': is_enabled
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@timetable_api.route('/api/timetable/school-status/<int:school_id>', methods=['GET'])
@company_admin_required
def get_school_timetable_status(school_id):
    """
    Company Admin: Get timetable module status for a school
    """
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            SELECT is_enabled, number_of_periods, created_at, updated_at
            FROM timetable_settings 
            WHERE school_id = ?
        ''', (school_id,))
        
        result = cursor.fetchone()
        
        if result:
            return jsonify({
                'success': True,
                'is_enabled': bool(result['is_enabled']),
                'number_of_periods': result['number_of_periods'],
                'created_at': result['created_at'],
                'updated_at': result['updated_at']
            })
        else:
            # No settings found, return default
            return jsonify({
                'success': True,
                'is_enabled': False,
                'number_of_periods': 8,
                'created_at': None,
                'updated_at': None
            })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@timetable_api.route('/api/timetable/all-schools-status', methods=['GET'])
@company_admin_required
def get_all_schools_timetable_status():
    """
    Company Admin: Get timetable status for all schools
    """
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            SELECT 
                s.id,
                s.name,
                s.address,
                s.contact_email,
                COALESCE(ts.is_enabled, 0) as is_enabled,
                COALESCE(ts.number_of_periods, 8) as number_of_periods,
                ts.updated_at
            FROM schools s
            LEFT JOIN timetable_settings ts ON s.id = ts.school_id
            WHERE s.is_hidden = 0
            ORDER BY s.name
        ''')
        
        schools = []
        for row in cursor.fetchall():
            schools.append({
                'id': row['id'],
                'name': row['name'],
                'address': row['address'],
                'contact_email': row['contact_email'],
                'timetable_enabled': bool(row['is_enabled']),
                'number_of_periods': row['number_of_periods'],
                'last_updated': row['updated_at']
            })
        
        return jsonify({
            'success': True,
            'schools': schools
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== SCHOOL ADMIN ENDPOINTS ====================

@timetable_api.route('/api/timetable/check-access', methods=['GET'])
def check_timetable_access():
    """
    Check if current user has access to timetable module
    """
    try:
        user_type = session.get('user_type')
        school_id = session.get('school_id')
        
        if user_type == 'company_admin':
            return jsonify({
                'success': True,
                'has_access': True,
                'role': 'company_admin'
            })
        
        if user_type == 'admin' and school_id:
            db = get_db()
            cursor = db.cursor()
            
            cursor.execute('''
                SELECT is_enabled FROM timetable_settings WHERE school_id = ?
            ''', (school_id,))
            
            result = cursor.fetchone()
            is_enabled = bool(result['is_enabled']) if result else False
            
            return jsonify({
                'success': True,
                'has_access': is_enabled,
                'role': 'admin'
            })
        
        if user_type == 'staff' and school_id:
            db = get_db()
            cursor = db.cursor()
            
            cursor.execute('''
                SELECT is_enabled FROM timetable_settings WHERE school_id = ?
            ''', (school_id,))
            
            result = cursor.fetchone()
            is_enabled = bool(result['is_enabled']) if result else False
            
            return jsonify({
                'success': True,
                'has_access': is_enabled,
                'role': 'staff'
            })
        
        return jsonify({
            'success': True,
            'has_access': False,
            'role': None
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== PERIOD MANAGEMENT ENDPOINTS ====================

@timetable_api.route('/api/timetable/periods', methods=['GET'])
def get_periods():
    """Get all periods for a school, optionally filtered by level/section"""
    try:
        school_id = request.args.get('school_id') or session.get('school_id')
        level_id = request.args.get('level_id')
        section_id = request.args.get('section_id')
        day_of_week = request.args.get('day_of_week')
        
        print(f"[DEBUG] get_periods - school_id: {school_id}, level_id: {level_id}, section_id: {section_id}, day_of_week: {day_of_week}")
        
        if not school_id:
            return jsonify({'success': False, 'error': 'School ID required'}), 400
            
        db = get_db()
        cursor = db.cursor()
        
        query = '''
            SELECT id, period_number, period_name, start_time, end_time, duration_minutes, level_id, section_id, day_of_week
            FROM timetable_periods 
            WHERE school_id = ?
        '''
        params = [school_id]
        
        if level_id and level_id != 'null':
            query += ' AND level_id = ?'
            params.append(level_id)
        if section_id and section_id != 'null':
            query += ' AND section_id = ?'
            params.append(section_id)
        if day_of_week and day_of_week != 'null':
            query += ' AND day_of_week = ?'
            params.append(day_of_week)
            
        query += ' ORDER BY day_of_week, period_number'
        
        cursor.execute(query, params)
        
        periods = []
        for row in cursor.fetchall():
            periods.append({
                'id': row['id'],
                'period_number': row['period_number'],
                'period_name': row['period_name'],
                'start_time': row['start_time'],
                'end_time': row['end_time'],
                'duration_minutes': row['duration_minutes'],
                'level_id': row['level_id'],
                'section_id': row['section_id'],
                'day_of_week': row['day_of_week']
            })
        
        print(f"[DEBUG] Returning {len(periods)} periods for school {school_id}")
            
        return jsonify({'success': True, 'periods': periods, 'data': periods})
    except Exception as e:
        print(f"[ERROR] get_periods: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@timetable_api.route('/api/timetable/period/save', methods=['POST'])
@admin_required
def save_period():
    """Create or update a period with hierarchical support"""
    try:
        data = request.get_json()
        school_id = data.get('school_id') or session.get('school_id')
        period_number = data.get('period_number')
        period_name = data.get('period_name')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        level_id = data.get('level_id')
        section_id = data.get('section_id')
        day_of_week = data.get('day_of_week')
        
        if not all([school_id, start_time, end_time]):
            return jsonify({'success': False, 'error': 'Missing required fields: start_time, end_time'}), 400

        db = get_db()
        cursor = db.cursor()

        if not period_number:
            # Auto-generate next period number
            cursor.execute('''
                SELECT MAX(period_number) FROM timetable_periods
                WHERE school_id = ? AND COALESCE(level_id, 0) = COALESCE(?, 0)
                AND COALESCE(section_id, 0) = COALESCE(?, 0)
                AND COALESCE(day_of_week, -1) = COALESCE(?, -1)
            ''', (school_id, level_id, section_id, day_of_week))
            max_val = cursor.fetchone()[0]
            period_number = (max_val or 0) + 1
            
        # Calculate duration
        try:
            start = datetime.strptime(start_time, '%H:%M')
            end = datetime.strptime(end_time, '%H:%M')
            duration = int((end - start).total_seconds() / 60)
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid time format. Use HH:MM'}), 400

        # Check if exists (UPSERT-like behavior)
        # Note: If day_of_week is provided, we check for match including day
        cursor.execute('''
            SELECT id FROM timetable_periods 
            WHERE school_id = ? AND COALESCE(level_id, 0) = COALESCE(?, 0) 
            AND COALESCE(section_id, 0) = COALESCE(?, 0) 
            AND COALESCE(day_of_week, -1) = COALESCE(?, -1)
            AND period_number = ?
        ''', (school_id, level_id, section_id, day_of_week, period_number))
        
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute('''
                UPDATE timetable_periods SET
                period_name = ?, start_time = ?, end_time = ?, 
                duration_minutes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (period_name, start_time, end_time, duration, existing['id']))
        else:
            cursor.execute('''
                INSERT INTO timetable_periods 
                (school_id, level_id, section_id, day_of_week, period_number, period_name, start_time, end_time, duration_minutes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (school_id, level_id, section_id, day_of_week, period_number, period_name, start_time, end_time, duration))
            
        db.commit()
        return jsonify({'success': True, 'message': 'Period saved successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@timetable_api.route('/api/timetable/next-period-number', methods=['GET'])
def get_next_period_number():
    """Auto-increment: Get the next period number for a Grade/Section"""
    try:
        school_id = request.args.get('school_id') or session.get('school_id')
        level_id = request.args.get('level_id')
        section_id = request.args.get('section_id')
        
        if not school_id:
            return jsonify({'success': False, 'error': 'School ID required'}), 400
            
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            SELECT MAX(period_number) FROM timetable_periods
            WHERE school_id = ? AND COALESCE(level_id, 0) = COALESCE(?, 0) 
            AND COALESCE(section_id, 0) = COALESCE(?, 0)
        ''', (school_id, level_id, section_id))
        
        max_period = cursor.fetchone()[0]
        next_period = (max_period or 0) + 1
        
        return jsonify({'success': True, 'next_period_number': next_period})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@timetable_api.route('/api/timetable/period/check-duplicate', methods=['GET'])
def check_duplicate_period():
    """Check if a period name already exists in a specific Grade/Section"""
    try:
        school_id = request.args.get('school_id') or session.get('school_id')
        level_id = request.args.get('level_id')
        section_id = request.args.get('section_id')
        period_name = request.args.get('period_name')
        
        if not all([school_id, period_name]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
            
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            SELECT id, period_number, start_time, end_time FROM timetable_periods
            WHERE school_id = ? AND COALESCE(level_id, 0) = COALESCE(?, 0) 
            AND COALESCE(section_id, 0) = COALESCE(?, 0) AND LOWER(period_name) = LOWER(?)
        ''', (school_id, level_id, section_id, period_name.strip()))
        
        existing = cursor.fetchone()
        
        if existing:
            return jsonify({
                'success': True, 
                'is_duplicate': True, 
                'period': {
                    'id': existing['id'],
                    'period_number': existing['period_number'],
                    'start_time': existing['start_time'],
                    'end_time': existing['end_time']
                }
            })
        
        return jsonify({'success': True, 'is_duplicate': False})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@timetable_api.route('/api/timetable/similar-periods', methods=['GET'])
def get_similar_periods():
    """Quick Fill: Find similar periods in other sections for suggestions"""
    try:
        school_id = request.args.get('school_id') or session.get('school_id')
        period_name = request.args.get('period_name')
        
        if not all([school_id, period_name]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
            
        db = get_db()
        cursor = db.cursor()
        
        # Find same period name in other levels/sections
        cursor.execute('''
            SELECT DISTINCT tp.start_time, tp.end_time, tal.level_name, ts.section_name
            FROM timetable_periods tp
            LEFT JOIN timetable_academic_levels tal ON tp.level_id = tal.id
            LEFT JOIN timetable_sections ts ON tp.section_id = ts.id
            WHERE tp.school_id = ? AND LOWER(tp.period_name) = LOWER(?)
            AND (tp.level_id IS NOT NULL OR tp.section_id IS NOT NULL)
            LIMIT 5
        ''', (school_id, period_name.strip()))
        
        suggestions = []
        for row in cursor.fetchall():
            source = f"{row['level_name'] or ''} {row['section_name'] or ''}".strip() or "Global"
            suggestions.append({
                'start_time': row['start_time'],
                'end_time': row['end_time'],
                'source': source
            })
            
        return jsonify({'success': True, 'suggestions': suggestions})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@timetable_api.route('/api/timetable/period/delete', methods=['POST'])
@admin_required
def delete_period():
    """Delete a period"""
    try:
        data = request.get_json()
        school_id = data.get('school_id') or session.get('school_id')
        period_id = data.get('period_id')
        
        if not period_id:
            return jsonify({'success': False, 'error': 'Period ID required'}), 400
            
        db = get_db()
        cursor = db.cursor()
        cursor.execute('DELETE FROM timetable_periods WHERE id = ? AND school_id = ?', (period_id, school_id))
        db.commit()
        
        return jsonify({'success': True, 'message': 'Period deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== DEPARTMENT PERMISSIONS ENDPOINTS ====================

@timetable_api.route('/api/timetable/departments', methods=['GET'])
def get_departments():
    """Get departments and their timetable permissions"""
    try:
        school_id = request.args.get('school_id') or session.get('school_id')
        if not school_id:
            return jsonify({'success': False, 'error': 'School ID required'}), 400
            
        db = get_db()
        cursor = db.cursor()
        
        # Get all unique departments from staff table for this school
        cursor.execute('SELECT DISTINCT department FROM staff WHERE school_id = ? AND department IS NOT NULL', (school_id,))
        all_depts = [row[0] for row in cursor.fetchall()]
        
        # Get existing permissions
        cursor.execute('SELECT department, allow_alterations, allow_inbound FROM timetable_department_permissions WHERE school_id = ?', (school_id,))
        permissions = {row[0]: {'allow_alterations': bool(row[1]), 'allow_inbound': bool(row[2])} for row in cursor.fetchall()}
        
        results = []
        for dept in all_depts:
            results.append({
                'department': dept,
                'allow_alterations': permissions.get(dept, {}).get('allow_alterations', True),
                'allow_inbound': permissions.get(dept, {}).get('allow_inbound', True)
            })
            
        return jsonify({'success': True, 'departments': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@timetable_api.route('/api/timetable/department/permission', methods=['POST'])
@timetable_api.route('/api/timetable/departments/permissions', methods=['POST'])
@admin_required
def update_department_permission():
    """Update timetable permissions for a department"""
    try:
        data = request.get_json()
        school_id = data.get('school_id') or session.get('school_id')
        department = data.get('department')
        allow_alterations = data.get('allow_alterations', True)
        allow_inbound = data.get('allow_inbound', True)
        
        if not department:
            return jsonify({'success': False, 'error': 'Department name required'}), 400
            
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
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
        return jsonify({'success': True, 'message': 'Permissions updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@timetable_api.route('/api/timetable/staff/list', methods=['GET'])
def get_staff_list():
    """Get list of staff for a school"""
    try:
        school_id = request.args.get('school_id') or session.get('school_id')
        if not school_id:
            return jsonify({'success': False, 'error': 'School ID required'}), 400
            
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT id, staff_id, full_name, department FROM staff WHERE school_id = ?', (school_id,))
        
        staff = []
        for row in cursor.fetchall():
            staff.append({
                'id': row['id'],
                'staff_id': row['staff_id'],
                'full_name': row['full_name'],
                'department': row['department']
            })
            
        return jsonify({'success': True, 'staff': staff})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== ASSIGNMENT & ALLOCATION ENDPOINTS ====================

@timetable_api.route('/api/timetable/assignments/all', methods=['GET'])
def get_all_assignments():
    """Get all assignments for a school (can filter by day)"""
    try:
        school_id = request.args.get('school_id') or session.get('school_id')
        day_of_week = request.args.get('day_of_week')
        
        if not school_id:
            return jsonify({'success': False, 'error': 'School ID required'}), 400
            
        db = get_db()
        cursor = db.cursor()
        
        query = '''
            SELECT ta.id, ta.staff_id, ta.day_of_week, ta.period_number, ta.class_subject, ta.is_locked,
                   s.full_name, s.department,
                   tp.period_name, tp.start_time, tp.end_time
            FROM timetable_assignments ta
            JOIN staff s ON ta.staff_id = s.id
            LEFT JOIN timetable_periods tp ON ta.school_id = tp.school_id AND ta.period_number = tp.period_number
            WHERE ta.school_id = ?
        '''
        params = [school_id]
        
        if day_of_week is not None:
            query += ' AND ta.day_of_week = ?'
            params.append(day_of_week)
            
        query += ' ORDER BY ta.day_of_week, ta.period_number'
        
        cursor.execute(query, params)
        assignments = []
        for row in cursor.fetchall():
            assignments.append({
                'id': row['id'],
                'staff_id': row['staff_id'],
                'day_of_week': row['day_of_week'],
                'period_number': row['period_number'],
                'class_subject': row['class_subject'],
                'is_locked': bool(row['is_locked']),
                'full_name': row['full_name'],
                'department': row['department'],
                'period_name': row['period_name'],
                'start_time': row['start_time'],
                'end_time': row['end_time']
            })
            
        return jsonify({'success': True, 'data': assignments})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@timetable_api.route('/api/timetable/assignment/override', methods=['POST'])
@admin_required
def admin_override_assignment():
    """Admin reassigns an existing assignment"""
    try:
        data = request.get_json()
        school_id = data.get('school_id') or session.get('school_id')
        assignment_id = data.get('assignment_id')
        new_staff_id = data.get('new_staff_id')
        notes = data.get('admin_notes', '')
        admin_id = session.get('user_id')
        
        if not all([assignment_id, new_staff_id]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
            
        db = get_db()
        cursor = db.cursor()
        
        # Verify assignment exists
        cursor.execute('SELECT * FROM timetable_assignments WHERE id = ? AND school_id = ?', (assignment_id, school_id))
        assignment = cursor.fetchone()
        if not assignment:
            return jsonify({'success': False, 'error': 'Assignment not found'}), 404
            
        # Update assignment
        cursor.execute('''
            UPDATE timetable_assignments SET
            staff_id = ?, is_locked = 1, locked_reason = ?, locked_by = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (new_staff_id, 'Admin Override: ' + notes, admin_id, assignment_id))
        
        db.commit()
        return jsonify({'success': True, 'message': 'Assignment overridden successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@timetable_api.route('/api/timetable/staff-period/list/<int:staff_id>', methods=['GET'])
def get_staff_allocations(staff_id):
    """Get all assignments for a specific staff member"""
    try:
        school_id = session.get('school_id')
        if not school_id:
             # If not in session, try to get from staff record
             db = get_db()
             cursor = db.cursor()
             cursor.execute('SELECT school_id FROM staff WHERE id = ?', (staff_id,))
             row = cursor.fetchone()
             if not row:
                 return jsonify({'success': False, 'error': 'Staff not found'}), 404
             school_id = row['school_id']

        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT ta.id, ta.day_of_week, ta.period_number, ta.class_subject, ta.created_at,
                   tp.period_name, tp.start_time, tp.end_time
            FROM timetable_assignments ta
            LEFT JOIN timetable_periods tp ON ta.school_id = tp.school_id AND ta.period_number = tp.period_number
            WHERE ta.staff_id = ? AND ta.school_id = ?
            ORDER BY ta.day_of_week, ta.period_number
        ''', (staff_id, school_id))
        
        allocations = []
        full_name = ""
        for row in cursor.fetchall():
            allocations.append({
                'assignment_id': row['id'], # Frontend expects assignment_id
                'period_number': row['period_number'], # Frontend expects period_number
                'day_of_week': row['day_of_week'],
                'day_name': ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][row['day_of_week']],
                'period_id': row['period_number'],
                'period_name': row['period_name'],
                'start_time': row['start_time'],
                'end_time': row['end_time'],
                'class_subject': row['class_subject'],
                'created_at': row['created_at']
            })
            
        # Get staff name
        cursor.execute('SELECT full_name FROM staff WHERE id = ?', (staff_id,))
        staff_row = cursor.fetchone()
        full_name = staff_row['full_name'] if staff_row else "Unknown"

        return jsonify({
            'success': True, 
            'periods': allocations, 
            'staff_name': full_name,
            'total_periods': len(allocations)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@timetable_api.route('/api/timetable/staff-period/assign', methods=['POST'])
@timetable_api.route('/api/timetable/assignment/save', methods=['POST'])
@admin_required
def assign_staff_period():
    """Assign a staff member to a period"""
    try:
        data = request.get_json()
        staff_id = data.get('staff_id')
        day_of_week = data.get('day_of_week')
        period_id = data.get('period_id') # Can be id from timetable_periods
        period_number = data.get('period_number') # Or direct period_number
        school_id = data.get('school_id') or session.get('school_id')
        
        if staff_id is None or day_of_week is None or (period_id is None and period_number is None):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
            
        db = get_db()
        cursor = db.cursor()
        
        # If period_id is provided, look up period_number
        if period_id is not None and period_number is None:
            cursor.execute('SELECT period_number FROM timetable_periods WHERE id = ?', (period_id,))
            period_row = cursor.fetchone()
            if not period_row:
                return jsonify({'success': False, 'message': 'Invalid period ID'}), 400
            period_number = period_row['period_number']
        
        # Check for conflict
        cursor.execute('''
            SELECT id FROM timetable_assignments 
            WHERE school_id = ? AND staff_id = ? AND day_of_week = ? AND period_number = ?
        ''', (school_id, staff_id, day_of_week, period_number))
        
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Staff already assigned to this slot'}), 400
            
        # Create assignment
        cursor.execute('''
            INSERT INTO timetable_assignments (school_id, staff_id, day_of_week, period_number)
            VALUES (?, ?, ?, ?)
        ''', (school_id, staff_id, day_of_week, period_number))
        
        db.commit()
        return jsonify({'success': True, 'message': 'Period assigned successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@timetable_api.route('/api/timetable/staff-period/remove/<int:allocation_id>', methods=['POST'])
@timetable_api.route('/api/timetable/assignment/delete', methods=['POST'])
@admin_required
def remove_staff_period(allocation_id=None):
    """Remove a staff period assignment"""
    try:
        if allocation_id is None:
            data = request.get_json() or {}
            allocation_id = data.get('assignment_id')
            
        if not allocation_id:
            return jsonify({'success': False, 'message': 'Assignment ID required'}), 400
            
        school_id = session.get('school_id')
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('DELETE FROM timetable_assignments WHERE id = ? AND school_id = ?', (allocation_id, school_id))
        db.commit()
        
        return jsonify({'success': True, 'message': 'Assignment removed successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== STAFF SELF-SERVICE ENDPOINTS ====================

@timetable_api.route('/api/timetable/staff', methods=['GET'])
@timetable_api.route('/api/timetable/assignments/<int:target_staff_id>', methods=['GET'])
def get_personal_timetable(target_staff_id=None):
    """Get weekly timetable for the logged-in staff member"""
    try:
        staff_id = target_staff_id or request.args.get('staff_id') or session.get('user_id')
        
        # If staff_id is 0 and we have a session user_id, use that
        if str(staff_id) == '0' and session.get('user_id'):
            staff_id = session.get('user_id')
            
        school_id = request.args.get('school_id') or session.get('school_id')
        
        print(f"[DEBUG] get_personal_timetable - staff_id: {staff_id}, school_id: {school_id}")
        
        if not staff_id or not school_id:
            return jsonify({'success': False, 'error': 'Unauthorized or missing params'}), 401
            
        db = get_db()
        cursor = db.cursor()
        
        # Get hierarchical assignments
        cursor.execute('''
            SELECT ha.id, ha.day_of_week, ha.period_number, ha.subject_name, ha.room_number,
                   ha.level_id, ha.section_id, ha.is_locked,
                   tp.period_name, tp.start_time, tp.end_time,
                   l.level_name, s.section_name
            FROM timetable_hierarchical_assignments ha
            LEFT JOIN timetable_periods tp ON ha.school_id = tp.school_id AND ha.period_number = tp.period_number
            LEFT JOIN timetable_academic_levels l ON ha.level_id = l.id
            LEFT JOIN timetable_sections s ON ha.section_id = s.id
            WHERE ha.staff_id = ? AND ha.school_id = ?
            ORDER BY ha.day_of_week, ha.period_number
        ''', (staff_id, school_id))
        
        timetable = []
        for row in cursor.fetchall():
            # Format class_subject as "Level Name - Section Name - Subject"
            level_name = row['level_name'] or f"Level {row['level_id']}"
            section_name = row['section_name'] or f"Section {row['section_id']}"
            subject = row['subject_name'] or 'Unknown Subject'
            class_subject = f"{level_name} - {section_name} - {subject}"
            
            timetable.append({
                'id': row['id'],
                'day_of_week': row['day_of_week'],
                'period_number': row['period_number'],
                'period_name': row['period_name'],
                'start_time': row['start_time'],
                'end_time': row['end_time'],
                'class_subject': class_subject,
                'room_number': row['room_number'],
                'is_locked': bool(row['is_locked']),
                'type': 'assigned'
            })
        
        print(f"[DEBUG] Found {len(timetable)} hierarchical assignments for staff {staff_id}")
            
        return jsonify({'success': True, 'timetable': timetable, 'data': timetable})
    except Exception as e:
        print(f"[ERROR] get_personal_timetable: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@timetable_api.route('/api/timetable/requests', methods=['GET'])
def get_swap_requests():
    """Get pending swap requests for the staff member"""
    try:
        staff_id = request.args.get('staff_id') or session.get('user_id')
        school_id = request.args.get('school_id') or session.get('school_id')
        
        print(f"[DEBUG] get_swap_requests - staff_id: {staff_id}, school_id: {school_id}")
        
        if not staff_id or not school_id:
            return jsonify({'success': False, 'error': 'Unauthorized or missing params'}), 401
            
        db = get_db()
        cursor = db.cursor()
        
        # Get received requests (updated to use hierarchical_assignments)
        cursor.execute('''
            SELECT tar.id, tar.requester_staff_id, s.full_name as requester_name, s.department as requester_dept,
                   tar.assignment_id, tar.reason, tar.status, tar.created_at,
                   tp.period_name, tp.start_time, tp.end_time, ha.period_number, ha.day_of_week,
                   ha.subject_name, l.level_name, sec.section_name
            FROM timetable_alteration_requests tar
            JOIN staff s ON tar.requester_staff_id = s.id
            JOIN timetable_hierarchical_assignments ha ON tar.assignment_id = ha.id
            LEFT JOIN timetable_periods tp ON ha.school_id = tp.school_id AND ha.period_number = tp.period_number
            LEFT JOIN timetable_academic_levels l ON ha.level_id = l.id
            LEFT JOIN timetable_sections sec ON ha.section_id = sec.id
            WHERE tar.target_staff_id = ? AND tar.school_id = ? AND tar.status = 'pending'
            ORDER BY tar.created_at DESC
        ''', (staff_id, school_id))
        
        requests = []
        for row in cursor.fetchall():
            # Format class_subject for display
            level_name = row['level_name'] or 'Unknown Level'
            section_name = row['section_name'] or 'Unknown Section'
            subject = row['subject_name'] or 'Unknown Subject'
            class_subject = f"{level_name} - {section_name} - {subject}"
            
            requests.append({
                'id': row['id'],
                'requester_id': row['requester_staff_id'],
                'requester_name': row['requester_name'],
                'requester_dept': row['requester_dept'],
                'assignment_id': row['assignment_id'],
                'period_name': row['period_name'],
                'period_number': row['period_number'],
                'day_of_week': row['day_of_week'],
                'start_time': row['start_time'],
                'end_time': row['end_time'],
                'class_subject': class_subject,
                'reason': row['reason'],
                'status': row['status'],
                'created_at': row['created_at']
            })
            
        print(f"[DEBUG] Returning {len(requests)} swap requests for staff {staff_id}")
        return jsonify({'success': True, 'requests': requests})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@timetable_api.route('/api/timetable/swap/request', methods=['POST'])
def request_swap():
    """Submit a swap request"""
    try:
        data = request.get_json()
        requester_id = session.get('user_id')
        school_id = session.get('school_id')
        assignment_id = data.get('assignment_id')
        target_staff_id = data.get('target_staff_id')
        reason = data.get('reason', '')
        
        if not all([assignment_id, target_staff_id]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
            
        db = get_db()
        cursor = db.cursor()
        
        # Check if requester owns the assignment (check hierarchical_assignments table)
        cursor.execute('SELECT staff_id FROM timetable_hierarchical_assignments WHERE id = ? AND school_id = ?', (assignment_id, school_id))
        assignment = cursor.fetchone()
        if not assignment or int(assignment['staff_id']) != int(requester_id):
            return jsonify({'success': False, 'error': 'Invalid assignment'}), 400
            
        cursor.execute('''
            INSERT INTO timetable_alteration_requests 
            (school_id, assignment_id, requester_staff_id, target_staff_id, alteration_type, reason, status)
            VALUES (?, ?, ?, ?, 'peer_swap', ?, 'pending')
        ''', (school_id, assignment_id, requester_id, target_staff_id, reason))
        
        db.commit()
        return jsonify({'success': True, 'message': 'Swap request sent successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@timetable_api.route('/api/timetable/swap/respond', methods=['POST'])
def respond_swap():
    """Accept or reject a swap request"""
    try:
        data = request.get_json()
        request_id = data.get('request_id')
        accept = data.get('accept', False)
        reason = data.get('response_reason', '')
        staff_id = session.get('user_id')
        
        if not request_id:
            return jsonify({'success': False, 'error': 'Request ID mandatory'}), 400
            
        db = get_db()
        cursor = db.cursor()
        
        # Verify target is the logged in user
        cursor.execute('SELECT * FROM timetable_alteration_requests WHERE id = ?', (request_id,))
        req_row = cursor.fetchone()
        if not req_row or int(req_row['target_staff_id']) != int(staff_id):
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
            
        status = 'accepted' if accept else 'rejected'
        cursor.execute('''
            UPDATE timetable_alteration_requests 
            SET status = ?, response_reason = ?, responded_by = ?, responded_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, reason, staff_id, request_id))
        
        if accept:
            # Swap the staff on the assignment (use hierarchical_assignments table)
            cursor.execute('''
                UPDATE timetable_hierarchical_assignments 
                SET staff_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (staff_id, req_row['assignment_id']))
            
        db.commit()
        return jsonify({'success': True, 'message': f'Request {status} successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@timetable_api.route('/api/timetable/allocations', methods=['GET'])
def get_personal_allocations():
    """Get all self-allocations for the logged-in staff member"""
    try:
        staff_id = request.args.get('staff_id') or session.get('user_id')
        school_id = request.args.get('school_id') or session.get('school_id')
        
        if not staff_id or not school_id:
            return jsonify({'success': False, 'error': 'Unauthorized or missing params'}), 401
            
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT tsa.*, tp.period_name, tp.start_time, tp.end_time
            FROM timetable_self_allocations tsa
            LEFT JOIN timetable_periods tp ON tsa.school_id = tp.school_id AND tsa.period_number = tp.period_number
            WHERE tsa.staff_id = ? AND tsa.school_id = ?
            ORDER BY tsa.day_of_week, tsa.period_number
        ''', (staff_id, school_id))
        
        allocations = []
        for row in cursor.fetchall():
            allocations.append({
                'id': row['id'],
                'day_of_week': row['day_of_week'],
                'period_number': row['period_number'],
                'period_name': row['period_name'],
                'start_time': row['start_time'],
                'end_time': row['end_time'],
                'class_subject': row['class_subject'],
                'is_admin_locked': bool(row['is_admin_locked'])
            })
            
        return jsonify({'success': True, 'allocations': allocations, 'data': allocations})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@timetable_api.route('/api/timetable/allocation/save', methods=['POST'])
def save_allocation():
    """Staff fills an empty slot (self-allocation)"""
    try:
        data = request.get_json()
        staff_id = session.get('user_id')
        school_id = session.get('school_id')
        day_of_week = data.get('day_of_week')
        period_number = data.get('period_number')
        class_subject = data.get('class_subject')
        
        if not all([day_of_week is not None, period_number, class_subject]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
            
        db = get_db()
        cursor = db.cursor()
        
        # Check if slot is already assigned or allocated
        cursor.execute('''
            SELECT id FROM timetable_assignments 
            WHERE school_id = ? AND day_of_week = ? AND period_number = ?
        ''', (school_id, day_of_week, period_number))
        if cursor.fetchone():
            return jsonify({'success': False, 'error': 'Slot already assigned'}), 400
            
        cursor.execute('''
            INSERT INTO timetable_self_allocations (school_id, staff_id, day_of_week, period_number, class_subject)
            VALUES (?, ?, ?, ?, ?)
        ''', (school_id, staff_id, day_of_week, period_number, class_subject))
        
        db.commit()
        return jsonify({'success': True, 'message': 'Slot allocated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@timetable_api.route('/api/timetable/allocation/update', methods=['POST'])
def update_allocation():
    """Update an existing self-allocation"""
    try:
        data = request.get_json()
        allocation_id = data.get('allocation_id')
        class_subject = data.get('class_subject')
        staff_id = session.get('user_id')
        
        if not allocation_id or not class_subject:
            return jsonify({'success': False, 'error': 'Missing fields'}), 400
            
        db = get_db()
        cursor = db.cursor()
        
        # Verify ownership and lock status
        cursor.execute('SELECT * FROM timetable_self_allocations WHERE id = ?', (allocation_id,))
        row = cursor.fetchone()
        if not row or int(row['staff_id']) != int(staff_id):
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        if row['is_admin_locked']:
            return jsonify({'success': False, 'error': 'Allocation is locked by admin'}), 403
            
        cursor.execute('''
            UPDATE timetable_self_allocations SET class_subject = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (class_subject, allocation_id))
        
        db.commit()
        return jsonify({'success': True, 'message': 'Allocation updated'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@timetable_api.route('/api/timetable/allocation/delete', methods=['POST'])
def delete_personal_allocation():
    """Delete a self-allocation (if not locked)"""
    try:
        data = request.get_json()
        allocation_id = data.get('allocation_id')
        staff_id = session.get('user_id')
        
        if not allocation_id:
            return jsonify({'success': False, 'error': 'Missing ID'}), 400
            
        db = get_db()
        cursor = db.cursor()
        
        # Verify ownership and lock status
        cursor.execute('SELECT * FROM timetable_self_allocations WHERE id = ?', (allocation_id,))
        row = cursor.fetchone()
        if not row or int(row['staff_id']) != int(staff_id):
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        if row['is_admin_locked']:
            return jsonify({'success': False, 'error': 'Cannot delete admin-locked allocation'}), 403
            
        cursor.execute('DELETE FROM timetable_self_allocations WHERE id = ?', (allocation_id,))
        db.commit()
        
        return jsonify({'success': True, 'message': 'Allocation deleted'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@timetable_api.route('/api/staff/available', methods=['GET'])
def get_available_staff():
    """Get staff members available for swap (same school, exclude self)"""
    try:
        school_id = request.args.get('school_id') or session.get('school_id')
        exclude_self = request.args.get('exclude_self', 'false').lower() == 'true'
        current_user_id = session.get('user_id')
        
        if not school_id:
            return jsonify({'success': False, 'error': 'School ID required'}), 400
            
        db = get_db()
        cursor = db.cursor()
        
        query = 'SELECT id, full_name, department FROM staff WHERE school_id = ?'
        params = [school_id]
        
        if exclude_self and current_user_id:
            query += ' AND id != ?'
            params.append(current_user_id)
            
        cursor.execute(query, params)
        staff = []
        for row in cursor.fetchall():
            staff.append({
                'id': row['id'],
                'full_name': row['full_name'],
                'department': row['department']
            })
            
        return jsonify({'success': True, 'staff': staff})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@timetable_api.route('/api/staff/available-for-period', methods=['GET'])
def get_available_staff_for_period():
    """Get staff members who are free at a specific day/period and in the same department"""
    try:
        school_id = request.args.get('school_id') or session.get('school_id')
        day_of_week = request.args.get('day_of_week', type=int)
        period_number = request.args.get('period_number', type=int)
        department = request.args.get('department')
        current_user_id = request.args.get('staff_id', type=int) or session.get('user_id')
        
        if not all([school_id, day_of_week, period_number, current_user_id]):
            return jsonify({'success': False, 'error': 'Missing required parameters'}), 400
            
        db = get_db()
        cursor = db.cursor()
        
        # If no department specified, use current user's department
        if not department:
            cursor.execute('SELECT department FROM staff WHERE id = ?', (current_user_id,))
            user_row = cursor.fetchone()
            if not user_row:
                return jsonify({'success': False, 'error': 'Staff member not found'}), 404
            department = user_row['department']
        
        # Get staff in specified department who are free at this period
        cursor.execute('''
            SELECT s.id, s.full_name, s.department
            FROM staff s
            WHERE s.school_id = ? 
                AND s.department = ?
                AND s.id != ?
                AND s.id NOT IN (
                    -- Staff who have an assignment at this time
                    SELECT staff_id FROM timetable_assignments 
                    WHERE school_id = ? 
                        AND day_of_week = ? 
                        AND period_number = ?
                    UNION
                    -- Staff who have a self-allocation at this time
                    SELECT staff_id FROM timetable_self_allocations
                    WHERE school_id = ? 
                        AND day_of_week = ? 
                        AND period_number = ?
                )
            ORDER BY s.full_name
        ''', (school_id, department, current_user_id, 
              school_id, day_of_week, period_number,
              school_id, day_of_week, period_number))
        
        staff = []
        for row in cursor.fetchall():
            staff.append({
                'id': row['id'],
                'full_name': row['full_name'],
                'department': row['department']
            })
            
        return jsonify({'success': True, 'staff': staff, 'count': len(staff)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@timetable_api.route('/api/departments', methods=['GET'])
def get_departments_for_school():
    """Get all unique departments in a school"""
    try:
        school_id = request.args.get('school_id') or session.get('school_id')
        
        if not school_id:
            return jsonify({'success': False, 'error': 'School ID required'}), 400
            
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            SELECT DISTINCT department 
            FROM staff 
            WHERE school_id = ? AND department IS NOT NULL AND department != ''
            ORDER BY department
        ''', (school_id,))
        
        departments = [row['department'] for row in cursor.fetchall()]
        
        return jsonify({'success': True, 'departments': departments, 'count': len(departments)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

