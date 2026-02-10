"""
Timetable Management API Routes
Provides REST endpoints for timetable CRUD operations, department permissions,
and staff self-service swap/allocation workflows.
"""

from flask import Blueprint, request, jsonify, session
from functools import wraps
from timetable_management import (
    TimetableManager,
    DepartmentPermissionManager,
    TimetableAssignmentManager,
    AlterationManager,
    SelfAllocationManager
)
from database import get_db
import logging

logger = logging.getLogger(__name__)

# Create Blueprint
timetable_bp = Blueprint('timetable', __name__, url_prefix='/api/timetable')

# ==================== AUTHENTICATION & AUTHORIZATION ====================

def check_admin_auth(f):
    """Decorator to ensure only school admins can access route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session['user_type'] != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized access. Admin required.'}), 401
        return f(*args, **kwargs)
    return decorated_function

def check_staff_auth(f):
    """Decorator to ensure only staff can access route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session['user_type'] != 'staff':
            return jsonify({'success': False, 'error': 'Unauthorized access. Staff login required.'}), 401
        return f(*args, **kwargs)
    return decorated_function

def check_auth_either(f):
    """Decorator to ensure user is logged in (admin or staff)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Unauthorized access. Login required.'}), 401
        return f(*args, **kwargs)
    return decorated_function

# ==================== HELPER FUNCTIONS ====================

def get_school_id():
    """Get school_id from session"""
    return session.get('school_id')

def get_user_id():
    """Get user_id from session"""
    return session.get('user_id')

# ==================== TIMETABLE SETTINGS ENDPOINTS ====================

@timetable_bp.route('/settings', methods=['GET'])
@check_auth_either
def get_timetable_settings():
    """Get timetable settings for the school"""
    try:
        school_id = get_school_id()
        manager = TimetableManager()
        
        result = manager.get_timetable_status(school_id)
        if result['success']:
            return jsonify({'success': True, 'settings': result['data']}), 200
        else:
            return jsonify({'success': False, 'error': result.get('error', 'Failed to retrieve settings')}), 400
    except Exception as e:
        logger.error(f"Error fetching timetable settings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@timetable_bp.route('/settings/toggle', methods=['POST'])
@check_admin_auth
def toggle_timetable_enabled():
    """Toggle timetable system enabled/disabled for school (Company Admin)"""
    try:
        school_id = get_school_id()
        is_enabled = request.json.get('is_enabled', False)
        
        manager = TimetableManager()
        if is_enabled:
            result = manager.enable_timetable_for_school(school_id)
        else:
            result = manager.disable_timetable_for_school(school_id)
        
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"Error toggling timetable: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== PERIOD MANAGEMENT ENDPOINTS ====================

@timetable_bp.route('/periods', methods=['GET'])
@check_admin_auth
def get_periods():
    """Get all periods for the school"""
    try:
        school_id = get_school_id()
        manager = TimetableManager()
        
        periods = manager.get_periods(school_id)
        return jsonify({'success': True, 'periods': periods}), 200
    except Exception as e:
        logger.error(f"Error fetching periods: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@timetable_bp.route('/period/save', methods=['POST'])
@check_admin_auth
def save_period():
    """Create or update a period"""
    try:
        school_id = get_school_id()
        data = request.json
        
        period_number = data.get('period_number')
        period_name = data.get('period_name')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        if not all([period_number, period_name, start_time, end_time]):
            return jsonify({'success': False, 'error': 'All fields are required'}), 400
        
        manager = TimetableManager()
        result = manager.create_period(school_id, period_number, period_name, start_time, end_time)
        
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"Error saving period: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@timetable_bp.route('/period/delete', methods=['POST'])
@check_admin_auth
def delete_period():
    """Delete a period"""
    try:
        school_id = get_school_id()
        period_id = request.json.get('period_id')
        
        if not period_id:
            return jsonify({'success': False, 'error': 'Period ID is required'}), 400
        
        manager = TimetableManager()
        result = manager.delete_period(school_id, period_id)
        
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"Error deleting period: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== DEPARTMENT PERMISSIONS ENDPOINTS ====================

@timetable_bp.route('/departments', methods=['GET'])
@check_admin_auth
def get_departments():
    """Get all departments and their permissions"""
    try:
        school_id = get_school_id()
        db = get_db()
        
        # Get list of departments from staff table
        depts = db.execute("""
            SELECT DISTINCT department FROM staff 
            WHERE school_id = ? AND department IS NOT NULL AND department != ''
            ORDER BY department
        """, (school_id,)).fetchall()
        
        department_list = [d['department'] for d in depts]
        
        # Get permission settings for each department
        manager = DepartmentPermissionManager()
        permissions = manager.get_department_permissions(school_id)
        
        # Merge department list with permission settings
        result = []
        for dept in department_list:
            perm = next((p for p in permissions if p.get('department') == dept), None)
            if perm:
                result.append(perm)
            else:
                # Default permissions if not set yet
                result.append({
                    'department': dept,
                    'allow_alterations': False,
                    'allow_inbound': False
                })
        
        return jsonify({'success': True, 'departments': result}), 200
    except Exception as e:
        logger.error(f"Error fetching departments: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@timetable_bp.route('/department/permission', methods=['POST'])
@check_admin_auth
def update_department_permission():
    """Update department permission settings"""
    try:
        school_id = get_school_id()
        data = request.json
        
        department = data.get('department')
        allow_alterations = data.get('allow_alterations', False)
        allow_inbound = data.get('allow_inbound', False)
        
        if not department:
            return jsonify({'success': False, 'error': 'Department is required'}), 400
        
        manager = DepartmentPermissionManager()
        result = manager.set_department_permission(
            school_id, department, allow_alterations, allow_inbound
        )
        
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"Error updating department permission: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== TIMETABLE ASSIGNMENT ENDPOINTS ====================

@timetable_bp.route('/assignment/delete', methods=['POST'])
@check_admin_auth
def delete_assignment():
    """Delete a staff assignment"""
    try:
        school_id = get_school_id()
        data = request.json
        assignment_id = data.get('assignment_id')
        
        if not assignment_id:
            return jsonify({'success': False, 'error': 'Assignment ID is required'}), 400
        
        db = get_db()
        db.execute("""
            DELETE FROM timetable_assignments 
            WHERE id = ? AND school_id = ?
        """, (assignment_id, school_id))
        db.commit()
        
        return jsonify({'success': True, 'message': 'Assignment deleted successfully'}), 200
    except Exception as e:
        logger.error(f"Error deleting assignment: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Get all assignments for a school
@timetable_bp.route('/assignments/all', methods=['GET'])
@check_admin_auth
def get_all_assignments():
    """Get all assignments for the school"""
    try:
        school_id = get_school_id()
        
        db = get_db()
        assignments = db.execute("""
            SELECT 
                ta.id,
                ta.staff_id,
                ta.day_of_week,
                ta.period_number,
                ta.is_locked,
                s.full_name as staff_name,
                tp.start_time,
                tp.end_time
            FROM timetable_assignments ta
            LEFT JOIN staff s ON ta.staff_id = s.id
            LEFT JOIN timetable_periods tp ON ta.period_number = tp.period_number AND ta.school_id = tp.school_id
            WHERE ta.school_id = ?
            ORDER BY ta.day_of_week, ta.period_number
        """, (school_id,)).fetchall()
        
        data = [{
            'id': a['id'],
            'staff_id': a['staff_id'],
            'staff_name': a['staff_name'],
            'day_of_week': a['day_of_week'],
            'period_number': a['period_number'],
            'start_time': a['start_time'],
            'end_time': a['end_time'],
            'is_locked': a['is_locked'],
            'full_name': a['staff_name']
        } for a in assignments]
        
        return jsonify({'success': True, 'data': data}), 200
    except Exception as e:
        logger.error(f"Error fetching assignments: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


    """Get assignments for a specific day"""
    try:
        school_id = get_school_id()
        day_of_week = request.args.get('day_of_week')
        
        if not day_of_week:
            return jsonify({'success': False, 'error': 'day_of_week is required'}), 400
        
        manager = TimetableAssignmentManager()
        assignments = manager.get_daily_timetable(school_id, day_of_week)
        
        return jsonify({'success': True, 'assignments': assignments}), 200
    except Exception as e:
        logger.error(f"Error fetching assignments: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@timetable_bp.route('/assignment/save', methods=['POST'])
@check_admin_auth
def save_assignment():
    """Create or update a staff assignment"""
    try:
        school_id = get_school_id()
        data = request.json
        
        staff_id = data.get('staff_id')
        day_of_week = data.get('day_of_week')
        period_number = data.get('period_number')
        
        if not all([staff_id, day_of_week, period_number]):
            return jsonify({'success': False, 'error': 'All fields are required'}), 400
        
        manager = TimetableAssignmentManager()
        result = manager.assign_staff_to_period(
            school_id, staff_id, day_of_week, period_number
        )
        
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"Error saving assignment: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@timetable_bp.route('/assignment/lock', methods=['POST'])
@check_admin_auth
def lock_assignment():
    """Lock a staff assignment (prevent self-alterations)"""
    try:
        school_id = get_school_id()
        admin_id = get_user_id()
        data = request.json
        
        assignment_id = data.get('assignment_id')
        is_locked = data.get('is_locked', True)
        
        if not assignment_id:
            return jsonify({'success': False, 'error': 'assignment_id is required'}), 400
        
        manager = TimetableAssignmentManager()
        result = manager.lock_assignment(school_id, assignment_id, is_locked, admin_id)
        
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"Error locking assignment: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@timetable_bp.route('/assignment/override', methods=['POST'])
@check_admin_auth
def admin_override():
    """Admin override: reassign a period to different staff"""
    try:
        school_id = get_school_id()
        admin_id = get_user_id()
        data = request.json
        
        assignment_id = data.get('assignment_id')
        new_staff_id = data.get('new_staff_id')
        reason = data.get('reason', 'Admin override')
        
        if not all([assignment_id, new_staff_id]):
            return jsonify({'success': False, 'error': 'assignment_id and new_staff_id are required'}), 400
        
        manager = TimetableAssignmentManager()
        result = manager.admin_override_assignment(
            school_id, assignment_id, new_staff_id, admin_id, reason
        )
        
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"Error performing admin override: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== STAFF TIMETABLE VIEW ENDPOINTS ====================

@timetable_bp.route('/staff/timetable', methods=['GET'])
@check_staff_auth
def get_staff_timetable():
    """Get staff member's weekly timetable"""
    try:
        school_id = get_school_id()
        staff_id = get_user_id()
        
        manager = TimetableAssignmentManager()
        timetable = manager.get_staff_timetable(school_id, staff_id)
        
        return jsonify({'success': True, 'timetable': timetable}), 200
    except Exception as e:
        logger.error(f"Error fetching staff timetable: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== SWAP REQUEST ENDPOINTS ====================

@timetable_bp.route('/swap/request', methods=['POST'])
@check_staff_auth
def request_swap():
    """Staff: Request swap with peer"""
    try:
        school_id = get_school_id()
        requester_staff_id = get_user_id()
        data = request.json
        
        assignment_id = data.get('assignment_id')
        target_staff_id = data.get('target_staff_id')
        reason = data.get('reason', '')
        
        if not all([assignment_id, target_staff_id]):
            return jsonify({'success': False, 'error': 'assignment_id and target_staff_id are required'}), 400
        
        manager = AlterationManager()
        result = manager.request_peer_swap(
            school_id, assignment_id, requester_staff_id, target_staff_id, reason
        )
        
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"Error requesting swap: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@timetable_bp.route('/swap/requests', methods=['GET'])
@check_staff_auth
def get_swap_requests():
    """Get pending swap requests for staff member"""
    try:
        school_id = get_school_id()
        staff_id = get_user_id()
        
        manager = AlterationManager()
        requests = manager.get_pending_requests(school_id, staff_id)
        
        return jsonify({'success': True, 'requests': requests}), 200
    except Exception as e:
        logger.error(f"Error fetching swap requests: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@timetable_bp.route('/swap/respond', methods=['POST'])
@check_staff_auth
def respond_to_swap():
    """Staff: Accept or reject swap request"""
    try:
        school_id = get_school_id()
        staff_id = get_user_id()
        data = request.json
        
        request_id = data.get('request_id')
        action = data.get('action')  # 'accept' or 'reject'
        
        if not request_id or action not in ['accept', 'reject']:
            return jsonify({'success': False, 'error': 'request_id and valid action are required'}), 400
        
        manager = AlterationManager()
        result = manager.respond_to_swap_request(school_id, request_id, staff_id, action)
        
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"Error responding to swap: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== SELF-ALLOCATION ENDPOINTS ====================

@timetable_bp.route('/allocations', methods=['GET'])
@check_staff_auth
def get_allocations():
    """Get staff member's self-allocations"""
    try:
        school_id = get_school_id()
        staff_id = get_user_id()
        
        manager = SelfAllocationManager()
        allocations = manager.get_staff_allocations(school_id, staff_id)
        
        return jsonify({'success': True, 'allocations': allocations}), 200
    except Exception as e:
        logger.error(f"Error fetching allocations: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@timetable_bp.route('/allocation/save', methods=['POST'])
@check_staff_auth
def save_allocation():
    """Staff: Self-allocate to an empty period"""
    try:
        school_id = get_school_id()
        staff_id = get_user_id()
        data = request.json
        
        day_of_week = data.get('day_of_week')
        period_number = data.get('period_number')
        
        if not all([day_of_week, period_number]):
            return jsonify({'success': False, 'error': 'day_of_week and period_number are required'}), 400
        
        manager = SelfAllocationManager()
        result = manager.allocate_to_empty_slot(
            school_id, staff_id, day_of_week, period_number
        )
        
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"Error saving allocation: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@timetable_bp.route('/allocation/update', methods=['POST'])
@check_staff_auth
def update_allocation():
    """Staff: Update their self-allocation (if not locked)"""
    try:
        school_id = get_school_id()
        staff_id = get_user_id()
        data = request.json
        
        allocation_id = data.get('allocation_id')
        new_period_number = data.get('new_period_number')
        
        if not all([allocation_id, new_period_number]):
            return jsonify({'success': False, 'error': 'allocation_id and new_period_number are required'}), 400
        
        manager = SelfAllocationManager()
        result = manager.update_allocation(
            school_id, allocation_id, staff_id, new_period_number
        )
        
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"Error updating allocation: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@timetable_bp.route('/allocation/delete', methods=['POST'])
@check_staff_auth
def delete_allocation():
    """Staff: Delete their self-allocation"""
    try:
        school_id = get_school_id()
        staff_id = get_user_id()
        allocation_id = request.json.get('allocation_id')
        
        if not allocation_id:
            return jsonify({'success': False, 'error': 'allocation_id is required'}), 400
        
        manager = SelfAllocationManager()
        result = manager.delete_allocation(school_id, allocation_id, staff_id)
        
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"Error deleting allocation: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== UTILITY ENDPOINTS ====================

@timetable_bp.route('/staff/available', methods=['GET'])
@check_staff_auth
def get_available_staff():
    """Get list of available staff for swap targeting"""
    try:
        school_id = get_school_id()
        day_of_week = request.args.get('day_of_week')
        period_number = request.args.get('period_number')
        
        db = get_db()
        
        # Get list of staff in same department
        current_staff = db.execute("""
            SELECT department FROM staff WHERE id = ? AND school_id = ?
        """, (get_user_id(), school_id)).fetchone()
        
        if not current_staff or not current_staff['department']:
            return jsonify({'success': False, 'error': 'Staff department not found'}), 400
        
        # Get staff with available slots on this day/period
        available = db.execute("""
            SELECT s.id, s.staff_id, s.full_name, s.department
            FROM staff s
            LEFT JOIN timetable_assignments ta ON 
                ta.staff_id = s.id 
                AND ta.day_of_week = ?
                AND ta.period_number = ?
                AND ta.school_id = ?
            WHERE s.school_id = ? 
            AND s.department = ?
            AND ta.id IS NULL
            ORDER BY s.full_name
        """, (day_of_week, period_number, school_id, school_id, current_staff['department'])).fetchall()
        
        staff_list = [{
            'id': s['id'],
            'staff_id': s['staff_id'],
            'full_name': s['full_name']
        } for s in available]
        
        return jsonify({'success': True, 'staff': staff_list}), 200
    except Exception as e:
        logger.error(f"Error fetching available staff: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@timetable_bp.route('/periods/<int:period_id>', methods=['GET'])
@check_auth_either
def get_period_details(period_id):
    """Get details of a specific period"""
    try:
        school_id = get_school_id()
        db = get_db()
        
        period = db.execute("""
            SELECT * FROM timetable_periods 
            WHERE id = ? AND school_id = ?
        """, (period_id, school_id)).fetchone()
        
        if not period:
            return jsonify({'success': False, 'error': 'Period not found'}), 404
        
        return jsonify({'success': True, 'period': dict(period)}), 200
    except Exception as e:
        logger.error(f"Error fetching period details: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@timetable_bp.route('/staff/list', methods=['GET'])
@check_admin_auth
def get_staff_list():
    """Get list of all staff for admin dropdowns"""
    try:
        school_id = get_school_id()
        db = get_db()
        
        staff = db.execute("""
            SELECT id, staff_id, full_name, department 
            FROM staff 
            WHERE school_id = ? AND is_active = 1
            ORDER BY CAST(staff_id AS INTEGER) ASC
        """, (school_id,)).fetchall()
        
        staff_list = [{
            'id': s['id'],
            'staff_id': s['staff_id'],
            'full_name': s['full_name'],
            'department': s['department']
        } for s in staff]
        
        return jsonify({'success': True, 'staff': staff_list}), 200
    except Exception as e:
        logger.error(f"Error fetching staff list: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== DEDICATED STAFF PERIOD ASSIGNMENT ====================

@timetable_bp.route('/staff-period/assign', methods=['POST'])
@check_admin_auth
def assign_period_to_staff():
    """
    Assign a specific period to a staff member for a particular day
    Separate endpoint for individual staff period assignment
    """
    try:
        school_id = get_school_id()
        data = request.json or {}
        
        staff_id = data.get('staff_id')
        day_of_week = data.get('day_of_week')
        period_number = data.get('period_number')
        
        if None in [staff_id, day_of_week, period_number]:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: staff_id, day_of_week, period_number'
            }), 400
        
        db = get_db()
        cursor = db.cursor()
        
        # Verify staff exists
        cursor.execute('SELECT id, full_name FROM staff WHERE id = ? AND school_id = ?', 
                      (staff_id, school_id))
        staff = cursor.fetchone()
        if not staff:
            return jsonify({'success': False, 'error': 'Staff member not found'}), 404
        
        # Check if already assigned to this period
        cursor.execute('''
            SELECT id FROM timetable_assignments
            WHERE school_id = ? AND staff_id = ? 
            AND day_of_week = ? AND period_number = ?
        ''', (school_id, staff_id, day_of_week, period_number))
        
        existing = cursor.fetchone()
        if existing:
            return jsonify({
                'success': False,
                'error': f'{staff[1]} is already assigned to this period'
            }), 400
        
        # Create assignment
        cursor.execute('''
            INSERT INTO timetable_assignments
            (school_id, staff_id, day_of_week, period_number, is_assigned)
            VALUES (?, ?, ?, ?, 1)
        ''', (school_id, staff_id, day_of_week, period_number))
        
        db.commit()
        
        return jsonify({
            'success': True,
            'assignment_id': cursor.lastrowid,
            'staff_name': staff[1],
            'day_of_week': day_of_week,
            'period_number': period_number,
            'message': f'Period assigned to {staff[1]} successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error assigning period to staff: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@timetable_bp.route('/staff-period/list/<int:staff_id>', methods=['GET'])
@check_admin_auth
def get_staff_assigned_periods(staff_id):
    """Get all periods assigned to a specific staff member"""
    try:
        school_id = get_school_id()
        db = get_db()
        cursor = db.cursor()
        
        # Verify staff exists
        cursor.execute('SELECT full_name FROM staff WHERE id = ? AND school_id = ?', 
                      (staff_id, school_id))
        staff = cursor.fetchone()
        if not staff:
            return jsonify({'success': False, 'error': 'Staff member not found'}), 404
        
        # Get all assigned periods
        cursor.execute('''
            SELECT ta.id, ta.day_of_week, ta.period_number, 
                   tp.start_time, tp.end_time, tp.period_name
            FROM timetable_assignments ta
            LEFT JOIN timetable_periods tp ON ta.period_number = tp.period_number 
                AND tp.school_id = ta.school_id
            WHERE ta.school_id = ? AND ta.staff_id = ?
            ORDER BY ta.day_of_week, ta.period_number
        ''', (school_id, staff_id))
        
        periods = []
        days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        
        for row in cursor.fetchall():
            periods.append({
                'assignment_id': row[0],
                'day_of_week': row[1],
                'day_name': days[row[1]],
                'period_number': row[2],
                'start_time': row[3],
                'end_time': row[4],
                'period_name': row[5]
            })
        
        return jsonify({
            'success': True,
            'staff_name': staff[0],
            'staff_id': staff_id,
            'periods': periods,
            'total_periods': len(periods)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching staff periods: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@timetable_bp.route('/staff-period/remove/<int:assignment_id>', methods=['POST'])
@check_admin_auth
def remove_staff_period_assignment(assignment_id):
    """Remove a period assignment from a staff member"""
    try:
        school_id = get_school_id()
        db = get_db()
        cursor = db.cursor()
        
        # Verify assignment exists
        cursor.execute('''
            SELECT ta.id, s.full_name, ta.day_of_week, ta.period_number
            FROM timetable_assignments ta
            JOIN staff s ON ta.staff_id = s.id
            WHERE ta.id = ? AND ta.school_id = ?
        ''', (assignment_id, school_id))
        
        assignment = cursor.fetchone()
        if not assignment:
            return jsonify({'success': False, 'error': 'Assignment not found'}), 404
        
        # Delete assignment
        cursor.execute('DELETE FROM timetable_assignments WHERE id = ? AND school_id = ?',
                      (assignment_id, school_id))
        db.commit()
        
        days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        
        return jsonify({
            'success': True,
            'message': f'Period removed from {assignment[1]} (Day: {days[assignment[2]]}, Period: {assignment[3]})',
            'staff_name': assignment[1]
        }), 200
        
    except Exception as e:
        logger.error(f"Error removing staff period assignment: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Export blueprint to be registered in main app
__all__ = ['timetable_bp']
