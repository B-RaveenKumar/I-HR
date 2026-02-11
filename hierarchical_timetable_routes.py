"""
Hierarchical Timetable API Routes
Provides REST endpoints for hierarchical timetable management with conflict detection
"""

from flask import Blueprint, request, jsonify, session
from functools import wraps
from hierarchical_timetable import HierarchicalTimetableManager
from database import get_db
import logging

logger = logging.getLogger(__name__)

# Create Blueprint
hierarchical_bp = Blueprint('hierarchical_timetable', __name__, url_prefix='/api/hierarchical-timetable')

# ==================== AUTHENTICATION DECORATORS ====================

def check_admin_auth(f):
    """Ensure only school admins can access route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session['user_type'] != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized access. Admin required.'}), 401
        return f(*args, **kwargs)
    return decorated_function

def check_staff_auth(f):
    """Ensure only staff can access route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session['user_type'] != 'staff':
            return jsonify({'success': False, 'error': 'Unauthorized access. Staff login required.'}), 401
        return f(*args, **kwargs)
    return decorated_function

def check_auth_either(f):
    """Ensure user is logged in (admin or staff)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Unauthorized access. Login required.'}), 401
        return f(*args, **kwargs)
    return decorated_function

# ==================== ORGANIZATION CONFIGURATION ====================

@hierarchical_bp.route('/organization/set-type', methods=['POST'])
@check_admin_auth
def set_organization_type():
    """Set organization type (School or College)"""
    try:
        school_id = session.get('school_id')
        data = request.json or {}
        org_type = data.get('organization_type', 'school')
        
        result = HierarchicalTimetableManager.set_organization_type(school_id, org_type)
        return jsonify(result), 200 if result['success'] else 400
    
    except Exception as e:
        logger.error(f"Error setting organization type: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@hierarchical_bp.route('/organization/config', methods=['GET'])
@check_auth_either
def get_organization_config():
    """Get organization configuration"""
    try:
        school_id = session.get('school_id')
        result = HierarchicalTimetableManager.get_organization_config(school_id)
        return jsonify(result), 200 if result['success'] else 400
    
    except Exception as e:
        logger.error(f"Error fetching organization config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== ACADEMIC LEVELS ====================

@hierarchical_bp.route('/levels', methods=['GET'])
@check_auth_either
def get_academic_levels():
    """Get all academic levels for school"""
    try:
        school_id = session.get('school_id')
        result = HierarchicalTimetableManager.get_academic_levels(school_id)
        return jsonify(result), 200 if result['success'] else 400
    
    except Exception as e:
        logger.error(f"Error fetching academic levels: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== SECTIONS MANAGEMENT ====================

@hierarchical_bp.route('/sections/create', methods=['POST'])
@check_admin_auth
def create_section():
    """Create a new section for an academic level"""
    try:
        school_id = session.get('school_id')
        data = request.json or {}
        
        level_id = data.get('level_id')
        section_name = data.get('section_name')
        capacity = data.get('capacity', 60)
        
        if not level_id or not section_name:
            return jsonify({'success': False, 'error': 'Missing required fields: level_id, section_name'}), 400
        
        result = HierarchicalTimetableManager.create_section(school_id, level_id, section_name, capacity)
        return jsonify(result), 200 if result['success'] else 400
    
    except Exception as e:
        logger.error(f"Error creating section: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@hierarchical_bp.route('/sections/level/<int:level_id>', methods=['GET'])
@check_auth_either
def get_sections_for_level(level_id):
    """Get all sections for a specific academic level"""
    try:
        result = HierarchicalTimetableManager.get_sections_for_level(level_id)
        return jsonify(result), 200 if result['success'] else 400
    
    except Exception as e:
        logger.error(f"Error fetching sections: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@hierarchical_bp.route('/sections/all', methods=['GET'])
@check_auth_either
def get_all_sections():
    """Get all sections for school"""
    try:
        school_id = session.get('school_id')
        result = HierarchicalTimetableManager.get_all_sections(school_id)
        return jsonify(result), 200 if result['success'] else 400
    
    except Exception as e:
        logger.error(f"Error fetching all sections: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@hierarchical_bp.route('/sections/<int:section_id>', methods=['DELETE'])
@check_admin_auth
def delete_section(section_id):
    """Delete a section"""
    try:
        school_id = session.get('school_id')
        result = HierarchicalTimetableManager.delete_section(school_id, section_id)
        return jsonify(result), 200 if result['success'] else 400
    
    except Exception as e:
        logger.error(f"Error deleting section: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== AVAILABILITY & CONFLICT CHECK ====================

@hierarchical_bp.route('/check-staff-availability', methods=['POST'])
@check_admin_auth
def check_staff_availability():
    """Check if staff is available for assignment (CONFLICT DETECTION)"""
    try:
        school_id = session.get('school_id')
        data = request.json or {}
        
        staff_id = data.get('staff_id')
        day_of_week = data.get('day_of_week')
        period_number = data.get('period_number')
        section_id = data.get('section_id')
        
        if None in [staff_id, day_of_week, period_number]:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: staff_id, day_of_week, period_number'
            }), 400
        
        result = HierarchicalTimetableManager.check_staff_availability(
            school_id, staff_id, day_of_week, period_number, section_id
        )
        
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"Error checking staff availability: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@hierarchical_bp.route('/check-section-availability', methods=['POST'])
@check_admin_auth
def check_section_availability():
    """Check if section is available for assignment"""
    try:
        school_id = session.get('school_id')
        data = request.json or {}
        
        section_id = data.get('section_id')
        day_of_week = data.get('day_of_week')
        period_number = data.get('period_number')
        
        if None in [section_id, day_of_week, period_number]:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: section_id, day_of_week, period_number'
            }), 400
        
        result = HierarchicalTimetableManager.check_section_availability(
            school_id, section_id, day_of_week, period_number
        )
        
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"Error checking section availability: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== ASSIGNMENT OPERATIONS ====================

@hierarchical_bp.route('/assign-staff', methods=['POST'])
@check_admin_auth
def assign_staff_to_period():
    """
    Assign staff to teach a section during a specific period
    CORE ASSIGNMENT ENDPOINT WITH VALIDATION
    """
    try:
        school_id = session.get('school_id')
        data = request.json or {}
        
        staff_id = data.get('staff_id')
        section_id = data.get('section_id')
        level_id = data.get('level_id')
        day_of_week = data.get('day_of_week')
        period_number = data.get('period_number')
        subject_name = data.get('subject_name')
        room_number = data.get('room_number')
        
        if None in [staff_id, section_id, level_id, day_of_week, period_number]:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: staff_id, section_id, level_id, day_of_week, period_number'
            }), 400
        
        result = HierarchicalTimetableManager.assign_staff_to_period(
            school_id, staff_id, section_id, level_id, day_of_week, 
            period_number, subject_name, room_number
        )
        
        return jsonify(result), 200 if result['success'] else 400
    
    except Exception as e:
        logger.error(f"Error assigning staff: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@hierarchical_bp.route('/assignment/<int:assignment_id>', methods=['DELETE'])
@check_admin_auth
def delete_assignment(assignment_id):
    """Delete a timetable assignment"""
    try:
        school_id = session.get('school_id')
        result = HierarchicalTimetableManager.delete_assignment(school_id, assignment_id)
        return jsonify(result), 200 if result['success'] else 400
    
    except Exception as e:
        logger.error(f"Error deleting assignment: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== SCHEDULE VIEWS ====================

@hierarchical_bp.route('/staff-schedule/<int:staff_id>', methods=['GET'])
@check_auth_either
def get_staff_schedule(staff_id):
    """
    Get complete schedule for a staff member
    STAFF VIEW ENDPOINT
    """
    try:
        school_id = session.get('school_id')
        result = HierarchicalTimetableManager.get_staff_schedule(school_id, staff_id)
        return jsonify(result), 200 if result['success'] else 400
    
    except Exception as e:
        logger.error(f"Error fetching staff schedule: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@hierarchical_bp.route('/section-schedule/<int:section_id>', methods=['GET'])
@check_auth_either
def get_section_schedule(section_id):
    """
    Get complete schedule for a section/class
    CLASS VIEW ENDPOINT
    """
    try:
        school_id = session.get('school_id')
        result = HierarchicalTimetableManager.get_section_schedule(school_id, section_id)
        return jsonify(result), 200 if result['success'] else 400
    
    except Exception as e:
        logger.error(f"Error fetching section schedule: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== COLOR-CODED GRID ====================

@hierarchical_bp.route('/grid/<item_type>/<int:item_id>', methods=['GET'])
@check_auth_either
def get_color_coded_grid(item_type, item_id):
    """
    Get color-coded grid for visualization
    
    item_type: 'staff' or 'section'
    item_id: Staff ID or Section ID
    """
    try:
        school_id = session.get('school_id')
        
        if item_type not in ['staff', 'section']:
            return jsonify({'success': False, 'error': 'Invalid item_type. Must be "staff" or "section"'}), 400
        
        result = HierarchicalTimetableManager.get_color_coded_grid(school_id, item_type, item_id)
        return jsonify(result), 200 if result['success'] else 400
    
    except Exception as e:
        logger.error(f"Error fetching color-coded grid: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== INITIALIZATION ====================

def register_hierarchical_timetable_routes(app):
    """Register the hierarchical timetable blueprint with the app"""
    app.register_blueprint(hierarchical_bp)
    logger.info("Hierarchical Timetable API routes registered successfully")
