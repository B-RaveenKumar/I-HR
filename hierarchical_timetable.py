"""
Hierarchical Timetable Management Module
Supports both School (Classes 1-12) and College (Years 1-4) modes
with dynamic section creation and staff conflict detection
"""

from database import get_db
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class HierarchicalTimetableManager:
    """Manages hierarchical timetable with conflict detection"""
    
    # ==================== ORGANIZATION CONFIGURATION ====================
    
    @staticmethod
    def set_organization_type(school_id, org_type):
        """
        Set organization type for school (school or college)
        
        Args:
            school_id (int): School identifier
            org_type (str): 'school' or 'college'
            
        Returns:
            dict: {success: bool, message: str}
        """
        try:
            db = get_db()
            cursor = db.cursor()
            
            if org_type not in ['school', 'college']:
                return {'success': False, 'error': 'Invalid organization type. Must be "school" or "college"'}
            
            total_levels = 12 if org_type == 'school' else 4
            level_type = 'class' if org_type == 'school' else 'year'
            
            cursor.execute('''
                INSERT OR REPLACE INTO timetable_organization_config 
                (school_id, organization_type, total_levels)
                VALUES (?, ?, ?)
            ''', (school_id, org_type, total_levels))
            
            # Also update schools table
            cursor.execute('''
                UPDATE schools SET organization_type = ? WHERE id = ?
            ''', (org_type, school_id))
            
            db.commit()
            
            # Generate default levels
            HierarchicalTimetableManager.generate_default_levels(school_id, org_type, total_levels)
            
            return {'success': True, 'message': f'Organization type set to {org_type}'}
        
        except Exception as e:
            logger.error(f"Error setting organization type: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_organization_config(school_id):
        """Get organization configuration for school"""
        try:
            db = get_db()
            cursor = db.cursor()
            
            cursor.execute('''
                SELECT organization_type, total_levels FROM timetable_organization_config
                WHERE school_id = ?
            ''', (school_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'success': True,
                    'data': {
                        'organization_type': row[0],
                        'total_levels': row[1]
                    }
                }
            
            return {'success': False, 'error': 'Organization config not found'}
        
        except Exception as e:
            logger.error(f"Error fetching organization config: {e}")
            return {'success': False, 'error': str(e)}
    
    # ==================== ACADEMIC LEVELS MANAGEMENT ====================
    
    @staticmethod
    def generate_default_levels(school_id, org_type, total_levels):
        """Generate default academic levels (Classes/Years)"""
        try:
            db = get_db()
            cursor = db.cursor()
            
            level_type = 'class' if org_type == 'school' else 'year'
            
            # Clear existing levels
            cursor.execute('DELETE FROM timetable_academic_levels WHERE school_id = ?', (school_id,))
            
            for i in range(1, total_levels + 1):
                if org_type == 'school':
                    level_name = f"Class {i}"
                    description = f"Class {i} - Standard {i}"
                else:
                    level_name = f"Year {i}"
                    description = f"Year {i} (Year {['I', 'II', 'III', 'IV'][i-1]})"
                
                cursor.execute('''
                    INSERT INTO timetable_academic_levels
                    (school_id, level_type, level_number, level_name, description)
                    VALUES (?, ?, ?, ?, ?)
                ''', (school_id, level_type, i, level_name, description))
            
            db.commit()
            return {'success': True, 'message': f'Generated {total_levels} academic levels'}
        
        except Exception as e:
            logger.error(f"Error generating levels: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_academic_levels(school_id):
        """Get all academic levels for school"""
        try:
            db = get_db()
            cursor = db.cursor()
            
            cursor.execute('''
                SELECT id, level_type, level_number, level_name, description, is_active
                FROM timetable_academic_levels
                WHERE school_id = ? AND is_active = 1
                ORDER BY level_number
            ''', (school_id,))
            
            levels = [dict(row) for row in cursor.fetchall()]
            return {'success': True, 'data': levels}
        
        except Exception as e:
            logger.error(f"Error fetching academic levels: {e}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def update_academic_level(school_id, level_id, level_name, description=None):
        """Update academic level name and description"""
        try:
            db = get_db()
            cursor = db.cursor()
            
            # Verify ownership
            cursor.execute('SELECT id FROM timetable_academic_levels WHERE id = ? AND school_id = ?', (level_id, school_id))
            if not cursor.fetchone():
                return {'success': False, 'error': 'Level not found or permission denied'}
            
            cursor.execute('''
                UPDATE timetable_academic_levels
                SET level_name = ?, description = ?
                WHERE id = ? AND school_id = ?
            ''', (level_name, description, level_id, school_id))
            
            db.commit()
            return {'success': True, 'message': 'Level updated successfully'}
            
        except Exception as e:
            logger.error(f"Error updating academic level: {e}")
            return {'success': False, 'error': str(e)}
    
    # ==================== SECTIONS MANAGEMENT ====================
    
    @staticmethod
    def create_section(school_id, level_id, section_name, capacity=60):
        """
        Create a new section for an academic level
        """
        if not school_id:
            logger.error("Create section failed: Missing school_id in session")
            return {'success': False, 'error': 'Authenticated session missing school_id. Please re-login.'}

        try:
            db = get_db()
            cursor = db.cursor()
            
            section_code = str(section_name).strip().upper().replace(" ", "_")
            if not section_code:
                return {'success': False, 'error': 'Invalid section name'}
            
            # Check for existing section in this level
            cursor.execute('''
                SELECT id FROM timetable_sections 
                WHERE school_id = ? AND level_id = ? AND section_code = ? AND is_active = 1
            ''', (school_id, level_id, section_code))
            
            if cursor.fetchone():
                return {'success': False, 'error': f'Section "{section_name}" already exists for this grade.'}
            
            cursor.execute('''
                INSERT INTO timetable_sections
                (school_id, level_id, section_name, section_code, capacity)
                VALUES (?, ?, ?, ?, ?)
            ''', (school_id, level_id, section_name, section_code, capacity))
            
            db.commit()
            
            logger.info(f"✅ Section {section_name} created for level {level_id} (School {school_id})")
            return {
                'success': True,
                'section_id': cursor.lastrowid,
                'message': f'Section {section_name} created successfully'
            }
        
        except Exception as e:
            logger.error(f"❌ Error creating section: {e}")
            return {'success': False, 'error': f"Database error: {str(e)}"}
    
    @staticmethod
    def get_sections_for_level(level_id):
        """Get all sections for an academic level"""
        try:
            db = get_db()
            cursor = db.cursor()
            
            cursor.execute('''
                SELECT id, school_id, level_id, section_name, section_code, capacity, is_active
                FROM timetable_sections
                WHERE level_id = ? AND is_active = 1
                ORDER BY section_name
            ''', (level_id,))
            
            sections = [dict(row) for row in cursor.fetchall()]
            return {'success': True, 'data': sections}
        
        except Exception as e:
            logger.error(f"Error fetching sections: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_all_sections(school_id):
        """Get all active sections for a school"""
        try:
            db = get_db()
            cursor = db.cursor()
            
            cursor.execute('''
                SELECT s.id, s.school_id, s.level_id, s.section_name, s.section_code,
                       s.capacity, l.level_number, l.level_name
                FROM timetable_sections s
                JOIN timetable_academic_levels l ON s.level_id = l.id
                WHERE s.school_id = ? AND s.is_active = 1
                ORDER BY l.level_number, s.section_name
            ''', (school_id,))
            
            sections = []
            for row in cursor.fetchall():
                sections.append({
                    'id': row[0],
                    'school_id': row[1],
                    'level_id': row[2],
                    'section_name': row[3],
                    'section_code': row[4],
                    'capacity': row[5],
                    'level_number': row[6],
                    'level_name': row[7]
                })
            
            return {'success': True, 'data': sections}
        
        except Exception as e:
            logger.error(f"Error fetching all sections: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def delete_section(school_id, section_id):
        """Delete a section (Deactivates it)"""
        try:
            db = get_db()
            cursor = db.cursor()
            
            # Check if section has active assignments
            cursor.execute('SELECT COUNT(*) FROM timetable_assignments WHERE section_id = ?', (section_id,))
            if cursor.fetchone()[0] > 0:
                return {'success': False, 'error': 'Cannot delete section with active timetable assignments'}
            
            cursor.execute('''
                UPDATE timetable_sections SET is_active = 0 
                WHERE id = ? AND school_id = ?
            ''', (section_id, school_id))
            
            db.commit()
            return {'success': True, 'message': 'Section deleted successfully'}
        
        except Exception as e:
            logger.error(f"Error deleting section: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== CONFLICT DETECTION ====================
    
    @staticmethod
    def check_staff_availability(school_id, staff_id, day_of_week, period_number, section_id=None, exclude_assignment_id=None):
        """
        Check if staff is available and not already assigned to another section
        CORE CONFLICT DETECTION LOGIC
        
        Args:
            school_id (int): School identifier
            staff_id (int): Staff member identifier
            day_of_week (int): Day (0-6)
            period_number (int): Period number
            section_id (int, optional): Section to check against
            exclude_assignment_id (int, optional): Assignment ID to exclude
            
        Returns:
            dict: {
                success: bool,
                is_available: bool,
                conflicts: [list of conflicting sections],
                reason: str
            }
        """
        try:
            db = get_db()
            cursor = db.cursor()
            
            # Check 1: Is staff marked as unavailable for this slot?
            cursor.execute('''
                SELECT reason_if_unavailable FROM timetable_staff_availability
                WHERE school_id = ? AND staff_id = ? AND day_of_week = ? AND period_number = ?
                AND is_available = 0
            ''', (school_id, staff_id, day_of_week, period_number))
            
            unavailable_row = cursor.fetchone()
            if unavailable_row:
                return {
                    'success': True,
                    'is_available': False,
                    'reason': f'Staff marked unavailable: {unavailable_row[0]}'
                }
            
            # Check 2: Does staff already have an assignment for this day/period?
            query = '''
                SELECT taa.id, ts.section_name, tal.level_name
                FROM timetable_hierarchical_assignments taa
                JOIN timetable_sections ts ON taa.section_id = ts.id
                JOIN timetable_academic_levels tal ON taa.level_id = tal.id
                WHERE taa.school_id = ? AND taa.staff_id = ? 
                AND taa.day_of_week = ? AND taa.period_number = ?
            '''
            params = [school_id, staff_id, day_of_week, period_number]
            
            if exclude_assignment_id:
                query += ' AND taa.id != ?'
                params.append(exclude_assignment_id)
            
            cursor.execute(query, params)
            conflicts = cursor.fetchall()
            
            if conflicts:
                conflicting_sections = [f"{row[1]} ({row[2]})" for row in conflicts]
                return {
                    'success': True,
                    'is_available': False,
                    'conflicts': conflicting_sections,
                    'reason': f'Staff already assigned to: {", ".join(conflicting_sections)}'
                }
            
            # Check 3: Is the maximum daily load exceeded?
            cursor.execute('''
                SELECT COUNT(*) FROM timetable_hierarchical_assignments
                WHERE school_id = ? AND staff_id = ? AND day_of_week = ?
            ''', (school_id, staff_id, day_of_week))
            
            max_classes_per_day = 6  # Configurable
            daily_load = cursor.fetchone()[0]
            if daily_load >= max_classes_per_day:
                return {
                    'success': True,
                    'is_available': False,
                    'reason': f'Maximum daily classes ({max_classes_per_day}) reached'
                }
            
            return {
                'success': True,
                'is_available': True,
                'reason': 'Staff is available'
            }
        
        except Exception as e:
            logger.error(f"Error checking staff availability: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def check_section_availability(school_id, section_id, day_of_week, period_number, exclude_assignment_id=None):
        """
        Check if a section already has a teacher assigned for the period
        
        Returns:
            dict: {success: bool, is_available: bool, assigned_staff: str, reason: str}
        """
        try:
            db = get_db()
            cursor = db.cursor()
            
            query = '''
                SELECT taa.id, s.full_name
                FROM timetable_hierarchical_assignments taa
                JOIN staff s ON taa.staff_id = s.id
                WHERE taa.school_id = ? AND taa.section_id = ? 
                AND taa.day_of_week = ? AND taa.period_number = ?
            '''
            params = [school_id, section_id, day_of_week, period_number]
            
            if exclude_assignment_id:
                query += ' AND taa.id != ?'
                params.append(exclude_assignment_id)
            
            cursor.execute(query, params)
            existing = cursor.fetchone()
            
            if existing:
                return {
                    'success': True,
                    'is_available': False,
                    'assigned_staff': existing[1],
                    'reason': f'Section already has {existing[1]} assigned'
                }
            
            return {
                'success': True,
                'is_available': True,
                'reason': 'Section slot is available'
            }
        
        except Exception as e:
            logger.error(f"Error checking section availability: {e}")
            return {'success': False, 'error': str(e)}
    
    # ==================== ASSIGNMENT MANAGEMENT ====================
    
    @staticmethod
    def assign_staff_to_period(school_id, staff_id, section_id, level_id, day_of_week, 
                               period_number, subject_name=None, room_number=None):
        """
        Assign staff to teach a section during a specific period
        IMPLEMENTS CORE ASSIGNMENT LOGIC WITH VALIDATION
        
        Args:
            school_id (int): School identifier
            staff_id (int): Staff member identifier
            section_id (int): Section identifier
            level_id (int): Academic level identifier
            day_of_week (int): Day (0-6)
            period_number (int): Period number
            subject_name (str): Subject/course name
            room_number (str): Room assignment
            
        Returns:
            dict: {success: bool, assignment_id: int, message: str, conflicts: list}
        """
        try:
            db = get_db()
            cursor = db.cursor()
            
            # Check staff availability
            staff_check = HierarchicalTimetableManager.check_staff_availability(
                school_id, staff_id, day_of_week, period_number, section_id
            )
            
            if not staff_check['success']:
                return staff_check
            
            if not staff_check['is_available']:
                return {
                    'success': False,
                    'error': staff_check.get('reason', 'Staff not available'),
                    'conflicts': staff_check.get('conflicts', [])
                }
            
            # Check section availability
            section_check = HierarchicalTimetableManager.check_section_availability(
                school_id, section_id, day_of_week, period_number
            )
            
            if not section_check['success']:
                return section_check
            
            if not section_check['is_available']:
                return {
                    'success': False,
                    'error': section_check.get('reason', 'Section not available')
                }
            
            # Create assignment
            cursor.execute('''
                INSERT INTO timetable_hierarchical_assignments
                (school_id, staff_id, section_id, level_id, day_of_week, period_number, 
                 subject_name, room_number, assignment_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'admin_assigned')
            ''', (school_id, staff_id, section_id, level_id, day_of_week, 
                  period_number, subject_name, room_number))
            
            db.commit()
            
            return {
                'success': True,
                'assignment_id': cursor.lastrowid,
                'message': 'Staff assigned to period successfully'
            }
        
        except Exception as e:
            logger.error(f"Error assigning staff to period: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_staff_schedule(school_id, staff_id):
        """
        Get complete schedule grid for a staff member
        DISPLAYS STAFF-SPECIFIC VIEW
        
        Returns:
            dict: {
                success: bool,
                data: {
                    schedule: [
                        {day: 0, period: 1, section: 'Class 10-A', time: '9:00-10:00', subject: 'Math'},
                        ...
                    ],
                    free_slots: [list],
                    conflicts: [list]
                }
            }
        """
        try:
            db = get_db()
            cursor = db.cursor()
            
            cursor.execute('''
                SELECT taa.id, taa.day_of_week, taa.period_number, 
                       ts.section_name, tal.level_name, taa.subject_name,
                       tp.start_time, tp.end_time, taa.room_number, taa.is_locked
                FROM timetable_hierarchical_assignments taa
                JOIN timetable_sections ts ON taa.section_id = ts.id
                JOIN timetable_academic_levels tal ON taa.level_id = tal.id
                JOIN timetable_periods tp ON taa.period_number = tp.period_number 
                    AND tp.school_id = taa.school_id
                    AND tp.level_id = taa.level_id
                    AND tp.section_id = taa.section_id
                WHERE taa.school_id = ? AND taa.staff_id = ?
                ORDER BY taa.day_of_week, taa.period_number
            ''', (school_id, staff_id))
            
            schedule = []
            for row in cursor.fetchall():
                schedule.append({
                    'assignment_id': row[0],
                    'day_of_week': row[1],
                    'period_number': row[2],
                    'section_name': row[3],
                    'level_name': row[4],
                    'subject_name': row[5],
                    'start_time': row[6],
                    'end_time': row[7],
                    'room_number': row[8],
                    'is_locked': row[9]
                })
            
            # Get conflict logs
            cursor.execute('''
                SELECT conflict_type, conflicting_sections, reason_if_unavailable, resolution_status
                FROM timetable_conflict_logs
                WHERE school_id = ? AND staff_id = ? AND resolution_status = 'pending'
            ''', (school_id, staff_id))
            
            conflicts = [dict(row) for row in cursor.fetchall()]
            
            return {
                'success': True,
                'data': {
                    'schedule': schedule,
                    'conflict_count': len(conflicts),
                    'conflicts': conflicts
                }
            }
        
        except Exception as e:
            logger.error(f"Error fetching staff schedule: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_section_schedule(school_id, section_id):
        """
        Get complete schedule grid for a section/class
        DISPLAYS CLASS-SPECIFIC VIEW
        
        Returns:
            dict: {
                success: bool,
                data: {
                    section_info: {name, level, capacity},
                    schedule: [
                        {day: 0, period: 1, staff: 'John Doe', subject: 'Math', time: '9:00-10:00'},
                        ...
                    ]
                }
            }
        """
        try:
            db = get_db()
            cursor = db.cursor()
            
            # Get section info
            cursor.execute('''
                SELECT ts.section_name, tal.level_name, tal.level_number, ts.capacity
                FROM timetable_sections ts
                JOIN timetable_academic_levels tal ON ts.level_id = tal.id
                WHERE ts.id = ? AND ts.school_id = ?
            ''', (section_id, school_id))
            
            section_info_row = cursor.fetchone()
            if not section_info_row:
                return {'success': False, 'error': 'Section not found'}
            
            section_info = {
                'section_name': section_info_row[0],
                'level_name': section_info_row[1],
                'level_number': section_info_row[2],
                'capacity': section_info_row[3]
            }
            
            # Get schedule
            cursor.execute('''
                SELECT taa.day_of_week, taa.period_number, s.full_name,
                       taa.subject_name, tp.start_time, tp.end_time, taa.room_number
                FROM timetable_hierarchical_assignments taa
                JOIN staff s ON taa.staff_id = s.id
                JOIN timetable_periods tp ON taa.period_number = tp.period_number 
                    AND tp.school_id = taa.school_id
                    AND tp.level_id = taa.level_id
                    AND tp.section_id = taa.section_id
                WHERE taa.school_id = ? AND taa.section_id = ?
                ORDER BY taa.day_of_week, taa.period_number
            ''', (school_id, section_id))
            
            schedule = []
            for row in cursor.fetchall():
                schedule.append({
                    'day_of_week': row[0],
                    'period_number': row[1],
                    'staff_name': row[2],
                    'subject_name': row[3],
                    'start_time': row[4],
                    'end_time': row[5],
                    'room_number': row[6]
                })
            
            return {
                'success': True,
                'data': {
                    'section_info': section_info,
                    'schedule': schedule
                }
            }
        
        except Exception as e:
            logger.error(f"Error fetching section schedule: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_color_coded_grid(school_id, item_type='staff', item_id=None):
        """
        Get color-coded grid display for visualization
        
        Args:
            item_type (str): 'staff' or 'section'
            item_id (int): Staff ID or Section ID
            
        Returns:
            dict: Grid structure for frontend visualization
        """
        try:
            DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            
            # Initialize grid (7 days x 8 periods)
            grid = {day: {} for day in DAYS}
            for day in DAYS:
                for period in range(1, 9):
                    grid[day][period] = {
                        'status': 'free',  # free, occupied, locked, conflict
                        'staff': '',
                        'section': '',
                        'subject': '',
                        'color': '#90EE90'  # Light green for free
                    }
            
            db = get_db()
            cursor = db.cursor()
            
            if item_type == 'staff':
                cursor.execute('''
                    SELECT taa.day_of_week, taa.period_number, s.full_name,
                           ts.section_name, tal.level_name, taa.subject_name, taa.is_locked
                    FROM timetable_hierarchical_assignments taa
                    JOIN timetable_sections ts ON taa.section_id = ts.id
                    JOIN timetable_academic_levels tal ON taa.level_id = tal.id
                    JOIN staff s ON taa.staff_id = s.id
                    WHERE taa.school_id = ? AND taa.staff_id = ?
                ''', (school_id, item_id))
            
            elif item_type == 'section':
                cursor.execute('''
                    SELECT taa.day_of_week, taa.period_number, s.full_name,
                           ts.section_name, tal.level_name, taa.subject_name, taa.is_locked
                    FROM timetable_hierarchical_assignments taa
                    JOIN timetable_sections ts ON taa.section_id = ts.id
                    JOIN timetable_academic_levels tal ON taa.level_id = tal.id
                    JOIN staff s ON taa.staff_id = s.id
                    WHERE taa.school_id = ? AND taa.section_id = ?
                ''', (school_id, item_id))
            
            for row in cursor.fetchall():
                day_idx = row[0]
                period = row[1]
                day_name = DAYS[day_idx]
                
                grid[day_name][period] = {
                    'status': 'locked' if row[6] else 'occupied',
                    'staff': row[2] if item_type == 'section' else '',
                    'section': f"{row[4]}-{row[3]}" if item_type == 'staff' else '',
                    'subject': row[5],
                    'color': '#FF6B6B' if row[6] else '#87CEEB'  # Red for locked, blue for occupied
                }
            
            return {
                'success': True,
                'data': grid
            }
        
        except Exception as e:
            logger.error(f"Error generating color-coded grid: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_all_assignments(school_id, day_of_week=None):
        """
        Get all hierarchical timetable assignments for a school
        """
        try:
            db = get_db()
            cursor = db.cursor()
            
            query = '''
                SELECT taa.id, taa.day_of_week, taa.period_number, 
                       ts.section_name, tal.level_name, taa.subject_name,
                       s.full_name, s.department,
                       tp.start_time, tp.end_time, taa.room_number, taa.is_locked
                FROM timetable_hierarchical_assignments taa
                JOIN timetable_sections ts ON taa.section_id = ts.id
                JOIN timetable_academic_levels tal ON taa.level_id = tal.id
                JOIN staff s ON taa.staff_id = s.id
                JOIN timetable_periods tp ON taa.period_number = tp.period_number 
                    AND tp.school_id = taa.school_id
                    AND tp.level_id = taa.level_id
                    AND tp.section_id = taa.section_id
                WHERE taa.school_id = ?
            '''
            params = [school_id]
            
            if day_of_week is not None:
                query += ' AND taa.day_of_week = ?'
                params.append(day_of_week)
            
            query += ' ORDER BY taa.day_of_week, taa.period_number'
            
            cursor.execute(query, params)
            
            assignments = []
            for row in cursor.fetchall():
                assignments.append({
                    'id': row[0],
                    'day_of_week': row[1],
                    'period_number': row[2],
                    'section_name': row[3],
                    'level_name': row[4],
                    'subject_name': row[5],
                    'full_name': row[6],
                    'department': row[7],
                    'start_time': row[8],
                    'end_time': row[9],
                    'room_number': row[10],
                    'is_locked': row[11]
                })
            
            return {'success': True, 'data': assignments}
            
        except Exception as e:
            logger.error(f"Error fetching all assignments: {e}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_all_staff_availability(school_id, day_of_week=None):
        """
        Get availability summary for all staff (Assigned vs Free periods)
        """
        try:
            db = get_db()
            cursor = db.cursor()
            
            # 1. Get all active staff
            cursor.execute("SELECT id, full_name, department FROM staff WHERE school_id = ? ORDER BY full_name", (school_id,))
            staff_list = [{'id': row[0], 'name': row[1], 'department': row[2]} for row in cursor.fetchall()]
            
            # 2. Get max periods (to define what "free" means)
            cursor.execute("SELECT MAX(period_number) FROM timetable_periods WHERE school_id = ?", (school_id,))
            row = cursor.fetchone()
            max_periods = (row[0] or 8) if row else 8
            
            # 3. Get all assignments
            query = "SELECT staff_id, day_of_week, period_number FROM timetable_hierarchical_assignments WHERE school_id = ?"
            params = [school_id]
            if day_of_week is not None:
                query += " AND day_of_week = ?"
                params.append(day_of_week)
            
            cursor.execute(query, params)
            assignments = cursor.fetchall()
            
            # Map: staff_id -> day -> set(periods)
            busy_map = {s['id']: {} for s in staff_list}
            for row in assignments:
                sid, day, pnum = row
                if sid in busy_map:
                    if day not in busy_map[sid]:
                        busy_map[sid][day] = set()
                    busy_map[sid][day].add(pnum)
            
            # 4. Build result
            result = []
            # logical days: if day_of_week specified, use it. Else use 1-6 (Mon-Sat)
            days_to_check = [int(day_of_week)] if day_of_week is not None else range(1, 7)
            
            for staff in staff_list:
                sid = staff['id']
                for day in days_to_check:
                    busy = busy_map[sid].get(day, set())
                    free = [p for p in range(1, max_periods + 1) if p not in busy]
                    
                    result.append({
                        'staff_id': sid,
                        'staff_name': staff['name'],
                        'department': staff['department'],
                        'day': day,
                        'total_assigned': len(busy),
                        'assigned_periods': sorted(list(busy)),
                        'free_periods': free
                    })
            
            return {'success': True, 'data': result}
            
        except Exception as e:
            logger.error(f"Error fetching staff availability: {e}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def delete_assignment(school_id, assignment_id):
        """Delete a hierarchical timetable assignment"""
        try:
            db = get_db()
            cursor = db.cursor()
            
            cursor.execute('''
                DELETE FROM timetable_hierarchical_assignments
                WHERE id = ? AND school_id = ?
            ''', (assignment_id, school_id))
            
            db.commit()
            
            return {
                'success': True,
                'message': 'Assignment deleted successfully'
            }
        
        except Exception as e:
            logger.error(f"Error deleting assignment: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def update_assignment(school_id, assignment_id, subject_name=None, room_number=None):
        """Update a hierarchical timetable assignment"""
        try:
            db = get_db()
            cursor = db.cursor()
            
            # First check if assignment exists
            cursor.execute('''
                SELECT id FROM timetable_hierarchical_assignments
                WHERE id = ? AND school_id = ?
            ''', (assignment_id, school_id))
            
            if not cursor.fetchone():
                return {'success': False, 'error': 'Assignment not found'}
            
            # Update fields
            updates = []
            params = []
            
            if subject_name is not None:
                updates.append('subject_name = ?')
                params.append(subject_name)
            
            if room_number is not None:
                updates.append('room_number = ?')
                params.append(room_number)
            
            if not updates:
                return {'success': False, 'error': 'No fields to update'}
            
            # Add assignment_id and school_id to params
            params.extend([assignment_id, school_id])
            
            query = f'''
                UPDATE timetable_hierarchical_assignments
                SET {', '.join(updates)}
                WHERE id = ? AND school_id = ?
            '''
            
            cursor.execute(query, params)
            db.commit()
            
            return {
                'success': True,
                'message': 'Assignment updated successfully'
            }
        
        except Exception as e:
            logger.error(f"Error updating assignment: {e}")
            return {'success': False, 'error': str(e)}
