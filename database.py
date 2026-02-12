# database.py
import sqlite3
from flask import g
import os

# Use instance/vishnorex.db - will be created in instance folder
DATABASE = os.path.join(os.path.dirname(__file__), 'instance', 'vishnorex.db')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db(app):
    os.makedirs(app.instance_path, exist_ok=True)

    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        # --- Table creation ---
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS schools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            contact_email TEXT,
            contact_phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            full_name TEXT,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id)
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER,
            staff_id TEXT NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            email TEXT,
            phone TEXT,
            department TEXT,
            position TEXT,
            gender TEXT,
            date_of_birth DATE,
            date_of_joining DATE,
            photo_data TEXT,
            shift_type TEXT DEFAULT 'general',
            basic_salary DECIMAL(10,2) DEFAULT 0.00,
            hra DECIMAL(10,2) DEFAULT 0.00,
            transport_allowance DECIMAL(10,2) DEFAULT 0.00,
            other_allowances DECIMAL(10,2) DEFAULT 0.00,
            pf_deduction DECIMAL(10,2) DEFAULT 0.00,
            esi_deduction DECIMAL(10,2) DEFAULT 0.00,
            professional_tax DECIMAL(10,2) DEFAULT 0.00,
            other_deductions DECIMAL(10,2) DEFAULT 0.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            UNIQUE(school_id, staff_id)
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id INTEGER NOT NULL,
            school_id INTEGER NOT NULL,
            date DATE NOT NULL,
            time_in TIME,
            time_out TIME,
            overtime_in TIME,
            overtime_out TIME,
            work_hours REAL DEFAULT 0,
            overtime_hours REAL DEFAULT 0,
            status TEXT CHECK(status IN ('present', 'absent', 'late', 'leave', 'left_soon', 'on_duty', 'holiday')),
            notes TEXT,
            on_duty_type TEXT,
            on_duty_location TEXT,
            on_duty_purpose TEXT,
            late_duration_minutes INTEGER DEFAULT 0,
            early_departure_minutes INTEGER DEFAULT 0,
            shift_type TEXT,
            shift_start_time TIME,
            shift_end_time TIME,
            regularization_requested BOOLEAN DEFAULT 0,
            regularization_status TEXT CHECK(regularization_status IN ('pending', 'approved', 'rejected')),
            regularization_reason TEXT,
            FOREIGN KEY (staff_id) REFERENCES staff(id),
            FOREIGN KEY (school_id) REFERENCES schools(id),
            UNIQUE(staff_id, date)
        )
        ''')

        # Create biometric verification log table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS biometric_verifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id INTEGER NOT NULL,
            school_id INTEGER NOT NULL,
            verification_type TEXT CHECK(verification_type IN ('check-in', 'check-out', 'overtime-in', 'overtime-out')) NOT NULL,
            verification_time DATETIME NOT NULL,
            device_ip TEXT,
            biometric_method TEXT CHECK(biometric_method IN ('fingerprint', 'face', 'card', 'password')),
            verification_status TEXT CHECK(verification_status IN ('success', 'failed', 'retry')) DEFAULT 'success',
            notes TEXT,
            FOREIGN KEY (staff_id) REFERENCES staff(id),
            FOREIGN KEY (school_id) REFERENCES schools(id)
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS leave_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id INTEGER NOT NULL,
            school_id INTEGER NOT NULL,
            leave_type TEXT CHECK(leave_type IN ('CL', 'SL', 'EL', 'ML')),
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            reason TEXT,
            status TEXT CHECK(status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_by INTEGER,
            processed_at TIMESTAMP,
            FOREIGN KEY (staff_id) REFERENCES staff(id),
            FOREIGN KEY (school_id) REFERENCES schools(id),
            FOREIGN KEY (processed_by) REFERENCES admins(id)
        )
        ''')

        # Create department shift mappings table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS department_shift_mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            department TEXT NOT NULL,
            default_shift_type TEXT NOT NULL CHECK(default_shift_type IN ('general', 'morning', 'evening', 'night')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            UNIQUE(school_id, department)
        )
        ''')

        # Create on-duty applications table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS on_duty_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id INTEGER NOT NULL,
            school_id INTEGER NOT NULL,
            duty_type TEXT CHECK(duty_type IN ('Official Work', 'Training', 'Meeting', 'Conference', 'Field Work', 'Other')) NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            start_time TIME,
            end_time TIME,
            location TEXT,
            purpose TEXT NOT NULL,
            reason TEXT,
            status TEXT CHECK(status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_by INTEGER,
            processed_at TIMESTAMP,
            admin_remarks TEXT,
            FOREIGN KEY (staff_id) REFERENCES staff(id),
            FOREIGN KEY (school_id) REFERENCES schools(id),
            FOREIGN KEY (processed_by) REFERENCES admins(id)
        )
        ''')

        # Create permission applications table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS permission_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id INTEGER NOT NULL,
            school_id INTEGER NOT NULL,
            permission_type TEXT CHECK(permission_type IN ('Personal Work', 'Medical', 'Emergency', 'Family Function', 'Other')) NOT NULL,
            permission_date DATE NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            duration_hours DECIMAL(4,2),
            reason TEXT NOT NULL,
            status TEXT CHECK(status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_by INTEGER,
            processed_at TIMESTAMP,
            admin_remarks TEXT,
            FOREIGN KEY (staff_id) REFERENCES staff(id),
            FOREIGN KEY (school_id) REFERENCES schools(id),
            FOREIGN KEY (processed_by) REFERENCES admins(id)
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS company_admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            full_name TEXT,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Create shift definitions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS shift_definitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shift_type TEXT NOT NULL UNIQUE,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            grace_period_minutes INTEGER DEFAULT 10,
            description TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Create attendance regularization requests table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance_regularization_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attendance_id INTEGER NOT NULL,
            staff_id INTEGER NOT NULL,
            school_id INTEGER NOT NULL,
            request_type TEXT CHECK(request_type IN ('late_arrival', 'early_departure')) NOT NULL,
            original_time TIME NOT NULL,
            expected_time TIME NOT NULL,
            duration_minutes INTEGER NOT NULL,
            staff_reason TEXT,
            admin_reason TEXT,
            status TEXT CHECK(status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_by INTEGER,
            processed_at TIMESTAMP,
            FOREIGN KEY (attendance_id) REFERENCES attendance(id),
            FOREIGN KEY (staff_id) REFERENCES staff(id),
            FOREIGN KEY (school_id) REFERENCES schools(id),
            FOREIGN KEY (processed_by) REFERENCES admins(id)
        )
        ''')

        # Create holidays table for comprehensive holiday management
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS holidays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            holiday_name TEXT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            holiday_type TEXT CHECK(holiday_type IN ('institution_wide', 'department_specific')) NOT NULL DEFAULT 'institution_wide',
            description TEXT,
            departments TEXT,  -- JSON array of department names for department-specific holidays
            is_recurring BOOLEAN DEFAULT 0,
            recurring_type TEXT CHECK(recurring_type IN ('yearly', 'monthly', 'weekly')),
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            FOREIGN KEY (created_by) REFERENCES admins(id)
        )
        ''')

        # Create weekly off configuration table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS weekly_off_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            day_of_week INTEGER NOT NULL CHECK(day_of_week BETWEEN 0 AND 6),  -- 0=Sunday, 1=Monday, ..., 6=Saturday
            is_enabled BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            UNIQUE(school_id, day_of_week)
        )
        ''')

        # Create comprehensive notifications table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            user_type TEXT NOT NULL CHECK(user_type IN ('admin', 'staff', 'company_admin')),
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            notification_type TEXT DEFAULT 'info' CHECK(notification_type IN ('info', 'success', 'warning', 'danger')),
            action_url TEXT,
            is_read BOOLEAN DEFAULT 0,
            read_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Create notification logs table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS notification_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            notification_type TEXT NOT NULL,
            recipient TEXT NOT NULL,
            subject TEXT,
            status TEXT NOT NULL CHECK(status IN ('sent', 'failed', 'pending')),
            error TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # --- TIMETABLE MANAGEMENT TABLES ---
        
        # School timetable settings table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL UNIQUE,
            is_enabled BOOLEAN DEFAULT 0,
            number_of_periods INTEGER DEFAULT 8,
            master_schedule TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id)
        )
        ''')

        # Master schedule periods table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable_periods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            level_id INTEGER,
            section_id INTEGER,
            period_number INTEGER NOT NULL,
            period_name TEXT,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            duration_minutes INTEGER,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            FOREIGN KEY (level_id) REFERENCES timetable_academic_levels(id),
            FOREIGN KEY (section_id) REFERENCES timetable_sections(id),
            UNIQUE(school_id, level_id, section_id, period_number)
        )
        ''')

        # Department alteration permissions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable_department_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            department TEXT NOT NULL,
            allow_alterations BOOLEAN DEFAULT 1,
            allow_inbound BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            UNIQUE(school_id, department)
        )
        ''')

        # Staff timetable assignments table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            staff_id INTEGER NOT NULL,
            day_of_week INTEGER NOT NULL CHECK(day_of_week BETWEEN 0 AND 6),
            period_number INTEGER NOT NULL,
            class_subject TEXT,
            is_assigned BOOLEAN DEFAULT 1,
            is_locked BOOLEAN DEFAULT 0,
            locked_reason TEXT,
            locked_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            FOREIGN KEY (staff_id) REFERENCES staff(id),
            FOREIGN KEY (locked_by) REFERENCES admins(id),
            UNIQUE(school_id, staff_id, day_of_week, period_number)
        )
        ''')

        # Alteration requests table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable_alteration_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            assignment_id INTEGER NOT NULL,
            requester_staff_id INTEGER NOT NULL,
            target_staff_id INTEGER,
            target_department TEXT,
            alteration_type TEXT CHECK(alteration_type IN ('peer_swap', 'self_allocation', 'admin_override')) DEFAULT 'peer_swap',
            status TEXT CHECK(status IN ('pending', 'accepted', 'rejected', 'admin_override')) DEFAULT 'pending',
            reason TEXT,
            response_reason TEXT,
            admin_notes TEXT,
            responded_by INTEGER,
            responded_at TIMESTAMP,
            processed_by INTEGER,
            processed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            FOREIGN KEY (assignment_id) REFERENCES timetable_assignments(id),
            FOREIGN KEY (requester_staff_id) REFERENCES staff(id),
            FOREIGN KEY (target_staff_id) REFERENCES staff(id),
            FOREIGN KEY (responded_by) REFERENCES staff(id),
            FOREIGN KEY (processed_by) REFERENCES admins(id)
        )
        ''')

        # Self-allocated periods (staff-filled empty slots) table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable_self_allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            staff_id INTEGER NOT NULL,
            day_of_week INTEGER NOT NULL CHECK(day_of_week BETWEEN 0 AND 6),
            period_number INTEGER NOT NULL,
            class_subject TEXT NOT NULL,
            is_admin_locked BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            FOREIGN KEY (staff_id) REFERENCES staff(id),
            UNIQUE(school_id, staff_id, day_of_week, period_number)
        )
        ''')

        # ==================== HIERARCHICAL TIMETABLE TABLES ====================
        
        # Organization type and level configuration table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable_organization_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL UNIQUE,
            organization_type TEXT CHECK(organization_type IN ('school', 'college')) DEFAULT 'school',
            total_levels INTEGER DEFAULT 12,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id)
        )
        ''')

        # Academic levels (Classes/Years) table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable_academic_levels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            level_type TEXT CHECK(level_type IN ('class', 'year')) DEFAULT 'class',
            level_number INTEGER NOT NULL,
            level_name TEXT NOT NULL,
            description TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            UNIQUE(school_id, level_number)
        )
        ''')

        # Dynamic sections for each academic level
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable_sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            level_id INTEGER NOT NULL,
            section_name TEXT NOT NULL,
            section_code TEXT NOT NULL,
            capacity INTEGER DEFAULT 60,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            FOREIGN KEY (level_id) REFERENCES timetable_academic_levels(id),
            UNIQUE(school_id, level_id, section_code)
        )
        ''')

        # Hierarchical timetable assignments (Staff to Section/Period/Level)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable_hierarchical_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            staff_id INTEGER NOT NULL,
            section_id INTEGER NOT NULL,
            level_id INTEGER NOT NULL,
            day_of_week INTEGER NOT NULL CHECK(day_of_week BETWEEN 0 AND 6),
            period_number INTEGER NOT NULL,
            subject_name TEXT,
            room_number TEXT,
            is_locked BOOLEAN DEFAULT 0,
            locked_by INTEGER,
            locked_reason TEXT,
            assignment_type TEXT CHECK(assignment_type IN ('admin_assigned', 'staff_self_allocated', 'substitute')) DEFAULT 'admin_assigned',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            FOREIGN KEY (staff_id) REFERENCES staff(id),
            FOREIGN KEY (section_id) REFERENCES timetable_sections(id),
            FOREIGN KEY (level_id) REFERENCES timetable_academic_levels(id),
            FOREIGN KEY (locked_by) REFERENCES admins(id),
            UNIQUE(school_id, section_id, day_of_week, period_number),
            UNIQUE(school_id, staff_id, section_id, day_of_week, period_number)
        )
        ''')

        # Conflict resolution and availability tracking
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable_staff_availability (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            staff_id INTEGER NOT NULL,
            day_of_week INTEGER NOT NULL CHECK(day_of_week BETWEEN 0 AND 6),
            period_number INTEGER NOT NULL,
            is_available BOOLEAN DEFAULT 1,
            reason_if_unavailable TEXT,
            updated_by INTEGER,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            FOREIGN KEY (staff_id) REFERENCES staff(id),
            FOREIGN KEY (updated_by) REFERENCES admins(id),
            UNIQUE(school_id, staff_id, day_of_week, period_number)
        )
        ''')

        # Conflict alerts and logs
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable_conflict_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            staff_id INTEGER NOT NULL,
            conflict_type TEXT CHECK(conflict_type IN ('double_booking', 'unavailable', 'capacity_exceeded')) DEFAULT 'double_booking',
            conflicting_sections TEXT,
            day_of_week INTEGER,
            period_number INTEGER,
            resolution_status TEXT CHECK(resolution_status IN ('pending', 'resolved', 'ignored')) DEFAULT 'pending',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            FOREIGN KEY (staff_id) REFERENCES staff(id)
        )
        ''')

        # --- Safe column additions ---
        def ensure_column_exists(table, column_def, column_name):
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            if column_name not in columns:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")

        ensure_column_exists('schools', 'logo_url TEXT', 'logo_url')
        ensure_column_exists('schools', 'is_hidden BOOLEAN DEFAULT 0', 'is_hidden')
        ensure_column_exists('staff', 'photo_url TEXT', 'photo_url')
        ensure_column_exists('staff', 'password_hash TEXT', 'password_hash')
        ensure_column_exists('staff', 'shift_type TEXT DEFAULT "general"', 'shift_type')

        # Add new staff fields for enhanced staff management
        ensure_column_exists('staff', 'first_name TEXT', 'first_name')
        ensure_column_exists('staff', 'last_name TEXT', 'last_name')
        ensure_column_exists('staff', 'date_of_birth DATE', 'date_of_birth')
        ensure_column_exists('staff', 'date_of_joining DATE', 'date_of_joining')
        ensure_column_exists('staff', 'destination TEXT', 'destination')
        ensure_column_exists('staff', 'gender TEXT CHECK(gender IN ("Male", "Female", "Other"))', 'gender')

        # Enhanced attendance tracking columns
        ensure_column_exists('attendance', 'late_duration_minutes INTEGER DEFAULT 0', 'late_duration_minutes')
        ensure_column_exists('attendance', 'early_departure_minutes INTEGER DEFAULT 0', 'early_departure_minutes')
        ensure_column_exists('attendance', 'shift_start_time TIME', 'shift_start_time')
        ensure_column_exists('attendance', 'shift_end_time TIME', 'shift_end_time')
        ensure_column_exists('attendance', 'regularization_requested BOOLEAN DEFAULT 0', 'regularization_requested')
        ensure_column_exists('attendance', 'regularization_status TEXT CHECK(regularization_status IN ("pending", "approved", "rejected")) DEFAULT NULL', 'regularization_status')
        ensure_column_exists('attendance', 'regularization_reason TEXT', 'regularization_reason')

        # Add hierarchical timetable support columns
        ensure_column_exists('schools', 'organization_type TEXT CHECK(organization_type IN ("school", "college")) DEFAULT "school"', 'organization_type')
        ensure_column_exists('timetable_settings', 'enable_hierarchical_timetable BOOLEAN DEFAULT 1', 'enable_hierarchical_timetable')
        ensure_column_exists('timetable_settings', 'weeks_per_cycle INTEGER DEFAULT 1', 'weeks_per_cycle')
        ensure_column_exists('timetable_settings', 'max_classes_per_staff_per_day INTEGER DEFAULT 6', 'max_classes_per_staff_per_day')
        ensure_column_exists('timetable_assignments', 'section_id INTEGER', 'section_id')
        ensure_column_exists('timetable_assignments', 'level_id INTEGER', 'level_id')
        ensure_column_exists('timetable_assignments', 'subject_name TEXT', 'subject_name')
        ensure_column_exists('timetable_assignments', 'room_number TEXT', 'room_number')
        ensure_column_exists('timetable_assignments', 'assignment_type TEXT CHECK(assignment_type IN ("admin_assigned", "staff_self_allocated", "substitute")) DEFAULT "admin_assigned"', 'assignment_type')

        # Add level_id and section_id to timetable_periods
        ensure_column_exists('timetable_periods', 'level_id INTEGER', 'level_id')
        ensure_column_exists('timetable_periods', 'section_id INTEGER', 'section_id')

        # Create cloud-related tables
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cloud_attendance_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            verification_type TEXT NOT NULL,
            punch_code INTEGER DEFAULT 0,
            status INTEGER DEFAULT 0,
            verify_method INTEGER DEFAULT 0,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cloud_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT UNIQUE NOT NULL,
            device_name TEXT NOT NULL,
            device_type TEXT DEFAULT 'ZK_BIOMETRIC',
            local_ip TEXT,
            local_port INTEGER DEFAULT 4370,
            cloud_enabled BOOLEAN DEFAULT TRUE,
            sync_interval INTEGER DEFAULT 30,
            last_sync TIMESTAMP,
            status TEXT DEFAULT 'unknown',
            organization_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cloud_sync_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            sync_type TEXT NOT NULL,
            records_count INTEGER DEFAULT 0,
            success BOOLEAN DEFAULT FALSE,
            error_message TEXT,
            sync_started_at TIMESTAMP,
            sync_completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_name TEXT NOT NULL,
            api_key TEXT UNIQUE NOT NULL,
            organization_id TEXT NOT NULL,
            permissions TEXT DEFAULT 'read',
            is_active BOOLEAN DEFAULT TRUE,
            expires_at TIMESTAMP,
            last_used_at TIMESTAMP,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS password_reset_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id INTEGER NOT NULL,
            school_id INTEGER NOT NULL,
            staff_name TEXT NOT NULL,
            staff_user_id TEXT NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved_at TIMESTAMP,
            approved_by INTEGER,
            FOREIGN KEY (staff_id) REFERENCES staff (id),
            FOREIGN KEY (school_id) REFERENCES schools (id),
            FOREIGN KEY (approved_by) REFERENCES admins (id)
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key TEXT UNIQUE NOT NULL,
            setting_value TEXT NOT NULL,
            description TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Initialize default shift definitions
        cursor.execute('SELECT COUNT(*) FROM shift_definitions')
        if cursor.fetchone()[0] == 0:
            # Insert default shift types as per requirements
            cursor.execute('''
                INSERT INTO shift_definitions (shift_type, start_time, end_time, grace_period_minutes, description)
                VALUES
                ('general', '09:00:00', '17:00:00', 15, 'General Institution Shift'),
                ('morning', '06:00:00', '14:00:00', 15, 'Morning Shift: 6:00 AM - 2:00 PM'),
                ('afternoon', '14:00:00', '22:00:00', 15, 'Afternoon Shift: 2:00 PM - 10:00 PM'),
                ('evening', '16:00:00', '00:00:00', 15, 'Evening Shift: 4:00 PM - 12:00 AM'),
                ('night', '22:00:00', '06:00:00', 15, 'Night Shift: 10:00 PM - 6:00 AM')
            ''')

        db.commit()


def get_institution_timings():
    """
    Get institution-wide check-in and check-out times from database.
    Returns dynamic timings if set, otherwise returns default times.
    
    Returns:
        dict: {
            'checkin_time': datetime.time object,
            'checkout_time': datetime.time object,
            'is_custom': bool (True if custom timings are set)
        }
    """
    import datetime
    
    try:
        db = get_db()
        
        # Check if institution_settings table exists
        cursor = db.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='institution_settings'
        """)
        
        if not cursor.fetchone():
            # Return default timings if table doesn't exist
            return {
                'checkin_time': datetime.time(9, 0),   # 9:00 AM
                'checkout_time': datetime.time(17, 0), # 5:00 PM
                'is_custom': False
            }
        
        # Fetch current institution timings
        cursor = db.execute("""
            SELECT setting_name, setting_value 
            FROM institution_settings 
            WHERE setting_name IN ('checkin_time', 'checkout_time')
        """)
        
        settings = dict(cursor.fetchall())
        
        if not settings or len(settings) < 2:
            # Return default timings if no custom settings found
            return {
                'checkin_time': datetime.time(9, 0),   # 9:00 AM
                'checkout_time': datetime.time(17, 0), # 5:00 PM
                'is_custom': False
            }
        
        # Parse time strings and return as time objects
        checkin_str = settings.get('checkin_time', '09:00')
        checkout_str = settings.get('checkout_time', '17:00')
        
        # Convert string to time object (format: HH:MM)
        checkin_time = datetime.datetime.strptime(checkin_str, '%H:%M').time()
        checkout_time = datetime.datetime.strptime(checkout_str, '%H:%M').time()
        
        return {
            'checkin_time': checkin_time,
            'checkout_time': checkout_time,
            'is_custom': True
        }
        
    except Exception as e:
        print(f"Error getting institution timings: {e}")
        # Return default timings on error
        return {
            'checkin_time': datetime.time(9, 0),   # 9:00 AM
            'checkout_time': datetime.time(17, 0), # 5:00 PM
            'is_custom': False
        }


def calculate_attendance_status(check_time, verification_type='check-in', grace_minutes=None, date_obj=None, department=None):
    """
    Calculate attendance status based on institution timings, considering holidays.

    Args:
        check_time (datetime.time): Time when staff checked in/out
        verification_type (str): 'check-in' or 'check-out'
        grace_minutes (int): Grace period in minutes for late arrival
        date_obj (datetime.date, optional): Date to check for holidays
        department (str, optional): Department for department-specific holidays

    Returns:
        str: Attendance status ('present', 'late', 'early_departure', 'holiday')
    """
    import datetime

    # Check if the date is a holiday
    if date_obj is None:
        date_obj = datetime.date.today()

    if is_holiday(date_obj, department):
        return 'holiday'

    timings = get_institution_timings()

    if verification_type == 'check-in':
        # Strict timing rule: any time after designated check-in is 'late'
        return 'late' if check_time > timings['checkin_time'] else 'present'

    elif verification_type == 'check-out':
        # For check-out, consider early departure
        return 'early_departure' if check_time < timings['checkout_time'] else 'present'

    else:
        return 'present'


def calculate_standard_working_hours_per_month():
    """
    Calculate standard working hours per month based on institution timing configuration.

    Returns:
        dict: {
            'daily_hours': float,
            'monthly_hours': float,
            'working_days_per_month': int
        }
    """
    import datetime
    import calendar

    try:
        # Get institution timings
        timings = get_institution_timings()
        checkin_time = timings['checkin_time']
        checkout_time = timings['checkout_time']

        # Calculate daily working hours
        checkin_dt = datetime.datetime.combine(datetime.date.today(), checkin_time)
        checkout_dt = datetime.datetime.combine(datetime.date.today(), checkout_time)

        # Handle overnight shifts (if checkout is before checkin)
        if checkout_dt < checkin_dt:
            checkout_dt += datetime.timedelta(days=1)

        daily_hours = (checkout_dt - checkin_dt).total_seconds() / 3600

        # Calculate working days per month (excluding Sundays and holidays)
        # Use current month as reference
        now = datetime.datetime.now()
        total_days = calendar.monthrange(now.year, now.month)[1]
        working_days = 0

        for day in range(1, total_days + 1):
            date_obj = datetime.date(now.year, now.month, day)
            # Exclude Sundays (weekday 6) and holidays
            if date_obj.weekday() != 6 and not is_holiday(date_obj):
                working_days += 1

        monthly_hours = daily_hours * working_days

        return {
            'daily_hours': daily_hours,
            'monthly_hours': monthly_hours,
            'working_days_per_month': working_days
        }

    except Exception as e:
        print(f"Error calculating standard working hours: {e}")
        # Return default values (8 hours/day, 26 working days/month)
        return {
            'daily_hours': 8.0,
            'monthly_hours': 208.0,  # 8 * 26
            'working_days_per_month': 26
        }


def calculate_hourly_rate(base_monthly_salary):
    """
    Calculate hourly rate from base monthly salary using institution timing configuration.

    Args:
        base_monthly_salary (float): Base monthly salary amount

    Returns:
        dict: {
            'hourly_rate': float,
            'daily_rate': float,
            'standard_monthly_hours': float,
            'standard_daily_hours': float
        }
    """
    try:
        base_salary = float(base_monthly_salary)
        if base_salary <= 0:
            return {
                'hourly_rate': 0.0,
                'daily_rate': 0.0,
                'standard_monthly_hours': 0.0,
                'standard_daily_hours': 0.0
            }

        # Get standard working hours
        working_hours = calculate_standard_working_hours_per_month()

        # Calculate rates
        hourly_rate = base_salary / working_hours['monthly_hours'] if working_hours['monthly_hours'] > 0 else 0
        daily_rate = base_salary / working_hours['working_days_per_month'] if working_hours['working_days_per_month'] > 0 else 0

        return {
            'hourly_rate': round(hourly_rate, 2),
            'daily_rate': round(daily_rate, 2),
            'standard_monthly_hours': working_hours['monthly_hours'],
            'standard_daily_hours': working_hours['daily_hours']
        }

    except Exception as e:
        print(f"Error calculating hourly rate: {e}")
        return {
            'hourly_rate': 0.0,
            'daily_rate': 0.0,
            'standard_monthly_hours': 0.0,
            'standard_daily_hours': 0.0
        }


def is_holiday(date_obj, department=None, school_id=None):
    """
    Check if a given date is a holiday.

    Args:
        date_obj (datetime.date): Date to check
        department (str, optional): Department name for department-specific holidays
        school_id (int, optional): School ID, defaults to current session school_id

    Returns:
        bool: True if the date is a holiday, False otherwise
    """
    import json
    from flask import session, has_request_context

    try:
        if school_id is None:
            if has_request_context():
                school_id = session.get('school_id')
            else:
                school_id = 1  # Default for testing

        if not school_id:
            return False

        db = get_db()

        # Check for institution-wide holidays
        institution_holidays = db.execute('''
            SELECT * FROM holidays
            WHERE school_id = ?
            AND holiday_type = 'institution_wide'
            AND is_active = 1
            AND ? BETWEEN start_date AND end_date
        ''', (school_id, date_obj.isoformat())).fetchall()

        if institution_holidays:
            return True

        # Check for department-specific holidays if department is provided
        if department:
            dept_holidays = db.execute('''
                SELECT * FROM holidays
                WHERE school_id = ?
                AND holiday_type = 'department_specific'
                AND is_active = 1
                AND ? BETWEEN start_date AND end_date
            ''', (school_id, date_obj.isoformat())).fetchall()

            for holiday in dept_holidays:
                if holiday['departments']:
                    try:
                        departments = json.loads(holiday['departments'])
                        if department in departments:
                            return True
                    except (json.JSONDecodeError, TypeError):
                        continue

        return False

    except Exception as e:
        print(f"Error checking holiday status: {e}")
        return False


def get_holidays(school_id=None, start_date=None, end_date=None, department=None):
    """
    Get holidays for a school within a date range.

    Args:
        school_id (int, optional): School ID, defaults to current session school_id
        start_date (str, optional): Start date in YYYY-MM-DD format
        end_date (str, optional): End date in YYYY-MM-DD format
        department (str, optional): Filter by department for department-specific holidays

    Returns:
        list: List of holiday records
    """
    import json
    from flask import session, has_request_context

    try:
        if school_id is None:
            if has_request_context():
                school_id = session.get('school_id')
            else:
                school_id = 1  # Default for testing

        if not school_id:
            return []

        db = get_db()

        # Build query conditions
        conditions = ['school_id = ?', 'is_active = 1']
        params = [school_id]

        if start_date:
            conditions.append('end_date >= ?')
            params.append(start_date)

        if end_date:
            conditions.append('start_date <= ?')
            params.append(end_date)

        query = f'''
            SELECT * FROM holidays
            WHERE {' AND '.join(conditions)}
            ORDER BY start_date ASC
        '''

        holidays = db.execute(query, params).fetchall()

        # Filter department-specific holidays if department is specified
        if department:
            filtered_holidays = []
            for holiday in holidays:
                if holiday['holiday_type'] == 'institution_wide':
                    filtered_holidays.append(holiday)
                elif holiday['holiday_type'] == 'department_specific' and holiday['departments']:
                    try:
                        departments = json.loads(holiday['departments'])
                        if department in departments:
                            filtered_holidays.append(holiday)
                    except (json.JSONDecodeError, TypeError):
                        continue
            return filtered_holidays

        return holidays

    except Exception as e:
        print(f"Error getting holidays: {e}")
        return []


def create_holiday(holiday_data):
    """
    Create a new holiday.

    Args:
        holiday_data (dict): Holiday information including name, dates, type, etc.

    Returns:
        dict: Result with success status and holiday_id or error message
    """
    import json
    from flask import session, has_request_context

    try:
        # Handle session data - use provided values or get from session
        if 'school_id' in holiday_data:
            school_id = holiday_data['school_id']
        elif has_request_context():
            school_id = session.get('school_id')
        else:
            return {'success': False, 'message': 'School ID required'}

        if 'created_by' in holiday_data:
            created_by = holiday_data['created_by']
        elif has_request_context():
            created_by = session.get('user_id')
        else:
            created_by = 1  # Default for testing

        if not school_id:
            return {'success': False, 'message': 'Invalid session or school ID'}

        db = get_db()

        # Validate required fields
        required_fields = ['holiday_name', 'start_date', 'end_date', 'holiday_type']
        for field in required_fields:
            if not holiday_data.get(field):
                return {'success': False, 'error': f'Missing required field: {field}'}

        # Prepare departments JSON
        departments_json = None
        if holiday_data.get('departments') and holiday_data['holiday_type'] == 'department_specific':
            departments_json = json.dumps(holiday_data['departments'])

        # Insert holiday
        cursor = db.execute('''
            INSERT INTO holidays (
                school_id, holiday_name, start_date, end_date, holiday_type,
                description, departments, is_recurring, recurring_type, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            school_id,
            holiday_data['holiday_name'],
            holiday_data['start_date'],
            holiday_data['end_date'],
            holiday_data['holiday_type'],
            holiday_data.get('description', ''),
            departments_json,
            holiday_data.get('is_recurring', 0),
            holiday_data.get('recurring_type'),
            created_by
        ))

        db.commit()

        return {
            'success': True,
            'holiday_id': cursor.lastrowid,
            'message': 'Holiday created successfully'
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}


def update_holiday(holiday_id, holiday_data):
    """
    Update an existing holiday.

    Args:
        holiday_id (int): Holiday ID to update
        holiday_data (dict): Updated holiday information

    Returns:
        dict: Result with success status and message
    """
    import json
    from flask import session, has_request_context

    try:
        # Handle session data - use provided values or get from session
        if 'school_id' in holiday_data:
            school_id = holiday_data['school_id']
        elif has_request_context():
            school_id = session.get('school_id')
        else:
            return {'success': False, 'message': 'School ID required'}

        if not school_id:
            return {'success': False, 'message': 'Invalid session or school ID'}

        db = get_db()

        # Check if holiday exists and belongs to the school
        existing_holiday = db.execute('''
            SELECT * FROM holidays WHERE id = ? AND school_id = ?
        ''', (holiday_id, school_id)).fetchone()

        if not existing_holiday:
            return {'success': False, 'error': 'Holiday not found'}

        # Prepare departments JSON
        departments_json = None
        if holiday_data.get('departments') and holiday_data.get('holiday_type') == 'department_specific':
            departments_json = json.dumps(holiday_data['departments'])

        # Update holiday
        db.execute('''
            UPDATE holidays SET
                holiday_name = ?,
                start_date = ?,
                end_date = ?,
                holiday_type = ?,
                description = ?,
                departments = ?,
                is_recurring = ?,
                recurring_type = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND school_id = ?
        ''', (
            holiday_data.get('holiday_name', existing_holiday['holiday_name']),
            holiday_data.get('start_date', existing_holiday['start_date']),
            holiday_data.get('end_date', existing_holiday['end_date']),
            holiday_data.get('holiday_type', existing_holiday['holiday_type']),
            holiday_data.get('description', existing_holiday['description']),
            departments_json,
            holiday_data.get('is_recurring', existing_holiday['is_recurring']),
            holiday_data.get('recurring_type', existing_holiday['recurring_type']),
            holiday_id,
            school_id
        ))

        db.commit()

        return {
            'success': True,
            'message': 'Holiday updated successfully'
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}


def delete_holiday(holiday_id):
    """
    Delete a holiday (soft delete by setting is_active to 0).

    Args:
        holiday_id (int): Holiday ID to delete

    Returns:
        dict: Result with success status and message
    """
    from flask import session

    try:
        school_id = session.get('school_id')

        if not school_id:
            return {'success': False, 'error': 'Invalid session'}

        db = get_db()

        # Check if holiday exists and belongs to the school
        existing_holiday = db.execute('''
            SELECT * FROM holidays WHERE id = ? AND school_id = ? AND is_active = 1
        ''', (holiday_id, school_id)).fetchone()

        if not existing_holiday:
            return {'success': False, 'error': 'Holiday not found'}

        # Soft delete holiday
        db.execute('''
            UPDATE holidays SET
                is_active = 0,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND school_id = ?
        ''', (holiday_id, school_id))

        db.commit()

        return {
            'success': True,
            'message': 'Holiday deleted successfully'
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_departments_list(school_id=None):
    """
    Get list of departments for the school.

    Args:
        school_id (int, optional): School ID, defaults to current session school_id

    Returns:
        list: List of department names
    """
    from flask import session, has_request_context

    try:
        if school_id is None:
            if has_request_context():
                school_id = session.get('school_id')
            else:
                school_id = 1  # Default for testing

        if not school_id:
            return []

        db = get_db()

        # Get unique departments from staff table
        departments = db.execute('''
            SELECT DISTINCT department FROM staff
            WHERE school_id = ? AND department IS NOT NULL AND department != ''
            ORDER BY department ASC
        ''', (school_id,)).fetchall()

        return [dept['department'] for dept in departments]

    except Exception as e:
        print(f"Error getting departments list: {e}")
        return []


def save_weekly_off_config(weekly_off_days, school_id=None):
    """
    Save weekly off configuration for a school.

    Args:
        weekly_off_days (list): List of day names (e.g., ['sunday', 'saturday'])
        school_id (int, optional): School ID, defaults to current session school_id

    Returns:
        dict: Result with success status and message
    """
    from flask import session, has_request_context

    try:
        if not school_id:
            if has_request_context():
                school_id = session.get('school_id')
            else:
                school_id = 1  # Default for testing

        if not school_id:
            return {'success': False, 'error': 'Invalid session'}

        db = get_db()

        # Day name to number mapping
        day_mapping = {
            'sunday': 0, 'monday': 1, 'tuesday': 2, 'wednesday': 3,
            'thursday': 4, 'friday': 5, 'saturday': 6
        }

        # Clear existing configuration for this school
        db.execute('DELETE FROM weekly_off_config WHERE school_id = ?', (school_id,))

        # Insert new configuration
        for day_name in weekly_off_days:
            day_name_lower = day_name.lower()
            if day_name_lower in day_mapping:
                day_number = day_mapping[day_name_lower]
                db.execute('''
                    INSERT INTO weekly_off_config (school_id, day_of_week, is_enabled)
                    VALUES (?, ?, 1)
                ''', (school_id, day_number))

        db.commit()

        return {
            'success': True,
            'message': 'Weekly off configuration saved successfully'
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_weekly_off_config(school_id=None):
    """
    Get weekly off configuration for a school.

    Args:
        school_id (int, optional): School ID, defaults to current session school_id

    Returns:
        dict: Result with success status and weekly off days
    """
    from flask import session, has_request_context

    try:
        if not school_id:
            if has_request_context():
                school_id = session.get('school_id')
            else:
                school_id = 1  # Default for testing

        if not school_id:
            return {'success': False, 'error': 'Invalid session'}

        db = get_db()

        # Get weekly off configuration
        config = db.execute('''
            SELECT day_of_week FROM weekly_off_config
            WHERE school_id = ? AND is_enabled = 1
            ORDER BY day_of_week
        ''', (school_id,)).fetchall()

        # Number to day name mapping
        day_names = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']

        weekly_off_days = [day_names[row['day_of_week']] for row in config]

        return {
            'success': True,
            'weekly_off_days': weekly_off_days
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}


def is_weekly_off_day(date, school_id=None):
    """
    Check if a given date is a weekly off day.

    Args:
        date (datetime.date or str): Date to check
        school_id (int, optional): School ID, defaults to current session school_id

    Returns:
        bool: True if the date is a weekly off day
    """
    from flask import session, has_request_context
    import datetime

    try:
        if not school_id:
            if has_request_context():
                school_id = session.get('school_id')
            else:
                school_id = 1  # Default for testing

        if not school_id:
            return False

        # Convert string date to datetime.date if needed
        if isinstance(date, str):
            date = datetime.datetime.strptime(date, '%Y-%m-%d').date()

        # Get day of week - Python's weekday() returns 0=Monday, 6=Sunday
        # We need to convert to JavaScript format: 0=Sunday, 1=Monday, ..., 6=Saturday
        python_weekday = date.weekday()  # 0=Monday, 1=Tuesday, ..., 6=Sunday
        our_weekday = (python_weekday + 1) % 7  # Convert: 0=Sunday, 1=Monday, ..., 6=Saturday

        db = get_db()

        # Check if this day is configured as weekly off
        result = db.execute('''
            SELECT COUNT(*) as count FROM weekly_off_config
            WHERE school_id = ? AND day_of_week = ? AND is_enabled = 1
        ''', (school_id, our_weekday)).fetchone()

        return result['count'] > 0

    except Exception as e:
        print(f"Error checking weekly off day: {e}")
        return False


# ===========================
# Department Management Functions
# ===========================

def create_departments_table():
    """Create the departments table if it doesn't exist"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            department_name TEXT NOT NULL,
            description TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            UNIQUE(school_id, department_name COLLATE NOCASE)
        )
        ''')
        
        db.commit()
        return True
    except Exception as e:
        print(f"Error creating departments table: {e}")
        return False


def initialize_default_departments(school_id):
    """Initialize default departments for a school if none exist"""
    try:
        # Create table if it doesn't exist
        create_departments_table()
        
        db = get_db()
        cursor = db.cursor()
        
        # Check if departments already exist for this school
        existing = cursor.execute(
            'SELECT COUNT(*) as count FROM departments WHERE school_id = ?',
            (school_id,)
        ).fetchone()
        
        if existing['count'] > 0:
            return True  # Departments already exist
        
        # Default departments to add
        default_departments = [
            ('Administration', 'Administrative staff and management'),
            ('Teaching', 'Teaching faculty and educators'),
            ('IT & Technology', 'Information technology and technical support'),
            ('Finance', 'Accounting, finance, and budgeting'),
            ('Human Resources', 'HR and personnel management'),
            ('Maintenance', 'Facilities and maintenance staff'),
            ('Library', 'Library staff and resources'),
            ('Security', 'Security and safety personnel')
        ]
        
        # Insert default departments
        for dept_name, description in default_departments:
            cursor.execute('''
                INSERT INTO departments (school_id, department_name, description)
                VALUES (?, ?, ?)
            ''', (school_id, dept_name, description))
        
        db.commit()
        print(f"Initialized {len(default_departments)} default departments for school_id {school_id}")
        return True
        
    except Exception as e:
        print(f"Error initializing default departments: {e}")
        db.rollback()
        return False


def get_all_departments(school_id):
    """Get all active departments for a school"""
    try:
        # Create table if it doesn't exist
        create_departments_table()
        
        db = get_db()
        cursor = db.cursor()
        
        departments = cursor.execute('''
            SELECT id, department_name, description
            FROM departments
            WHERE school_id = ? AND is_active = 1
            ORDER BY department_name
        ''', (school_id,)).fetchall()
        
        # Convert to list of dictionaries
        result = [dict(dept) for dept in departments]
        
        # If no departments exist, initialize defaults
        if not result:
            initialize_default_departments(school_id)
            # Fetch again after initialization
            departments = cursor.execute('''
                SELECT id, department_name, description
                FROM departments
                WHERE school_id = ? AND is_active = 1
                ORDER BY department_name
            ''', (school_id,)).fetchall()
            result = [dict(dept) for dept in departments]
        
        return result
        
    except Exception as e:
        print(f"Error fetching departments: {e}")
        # Return default list if database operation fails
        return [
            {'id': 0, 'department_name': 'Administration', 'description': ''},
            {'id': 0, 'department_name': 'Teaching', 'description': ''},
            {'id': 0, 'department_name': 'IT & Technology', 'description': ''},
            {'id': 0, 'department_name': 'Finance', 'description': ''}
        ]


def add_department(name, description, school_id):
    """Add a new department to the database"""
    db = None
    try:
        if not name or not name.strip():
            return {'success': False, 'message': 'Department name is required'}
        
        name = name.strip()
        
        # Create table if it doesn't exist
        create_departments_table()
        
        db = get_db()
        cursor = db.cursor()
        
        # Check for existing department (both active and inactive)
        existing = cursor.execute('''
            SELECT id, is_active FROM departments 
            WHERE school_id = ? AND LOWER(department_name) = LOWER(?)
        ''', (school_id, name)).fetchone()
        
        if existing:
            # If department exists and is inactive, reactivate it
            if existing['is_active'] == 0:
                cursor.execute('''
                    UPDATE departments 
                    SET is_active = 1, description = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND school_id = ?
                ''', (description or '', existing['id'], school_id))
                
                db.commit()
                
                return {
                    'success': True,
                    'message': f'Department "{name}" reactivated successfully',
                    'department_name': name
                }
            else:
                # Department exists and is active
                return {'success': False, 'message': 'Department already exists'}
        
        # Insert new department if it doesn't exist
        cursor.execute('''
            INSERT INTO departments (school_id, department_name, description)
            VALUES (?, ?, ?)
        ''', (school_id, name, description or ''))
        
        db.commit()
        
        return {
            'success': True,
            'message': f'Department "{name}" added successfully',
            'department_name': name
        }
        
    except Exception as e:
        print(f"Error adding department: {e}")
        if db:
            db.rollback()
        return {'success': False, 'message': f'Error adding department: {str(e)}'}


def delete_department(department_id, school_id):
    """Delete a department from the database"""
    db = None
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Check if department exists and belongs to this school
        existing = cursor.execute('''
            SELECT department_name FROM departments 
            WHERE id = ? AND school_id = ?
        ''', (department_id, school_id)).fetchone()
        
        if not existing:
            return {'success': False, 'message': 'Department not found'}
        
        department_name = existing['department_name']
        
        # Check if any staff members are assigned to this department
        staff_count = cursor.execute('''
            SELECT COUNT(*) as count FROM staff 
            WHERE school_id = ? AND department = ?
        ''', (school_id, department_name)).fetchone()
        
        if staff_count and staff_count['count'] > 0:
            return {
                'success': False, 
                'message': f'Cannot delete department "{department_name}". {staff_count["count"]} staff member(s) are assigned to it.'
            }
        
        # Soft delete: Set is_active to 0
        cursor.execute('''
            UPDATE departments 
            SET is_active = 0, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND school_id = ?
        ''', (department_id, school_id))
        
        db.commit()
        
        return {
            'success': True,
            'message': f'Department "{department_name}" deleted successfully'
        }
        
    except Exception as e:
        print(f"Error deleting department: {e}")
        if db:
            db.rollback()
        return {'success': False, 'message': f'Error deleting department: {str(e)}'}


# ===========================
# Position Management Functions
# ===========================

def create_positions_table():
    """Create the positions table if it doesn't exist"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            position_name TEXT NOT NULL,
            description TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id),
            UNIQUE(school_id, position_name COLLATE NOCASE)
        )
        ''')
        
        db.commit()
        return True
    except Exception as e:
        print(f"Error creating positions table: {e}")
        return False


def initialize_default_positions(school_id):
    """Initialize default positions for a school if none exist"""
    try:
        # Create table if it doesn't exist
        create_positions_table()
        
        db = get_db()
        cursor = db.cursor()
        
        # Check if positions already exist for this school
        existing = cursor.execute(
            'SELECT COUNT(*) as count FROM positions WHERE school_id = ?',
            (school_id,)
        ).fetchone()
        
        if existing['count'] > 0:
            return True  # Positions already exist
        
        # Default positions to add
        default_positions = [
            ('Teacher', 'Teaching staff and faculty members'),
            ('Principal', 'School principal and head administrator'),
            ('Vice Principal', 'Assistant to the principal'),
            ('HOD', 'Head of Department'),
            ('Coordinator', 'Department or program coordinator'),
            ('Lab Assistant', 'Laboratory technical assistant'),
            ('Librarian', 'Library management and services'),
            ('Accountant', 'Finance and accounting staff'),
            ('Office Administrator', 'Office management and administration'),
            ('Receptionist', 'Front desk and reception staff'),
            ('Clerk', 'Administrative clerk'),
            ('Peon', 'Support and housekeeping staff'),
            ('Security Guard', 'Security and safety personnel'),
            ('IT Support', 'Information technology support staff'),
            ('Counselor', 'Student counseling and guidance')
        ]
        
        # Insert default positions
        for position_name, description in default_positions:
            cursor.execute('''
                INSERT INTO positions (school_id, position_name, description)
                VALUES (?, ?, ?)
            ''', (school_id, position_name, description))
        
        db.commit()
        print(f"Initialized {len(default_positions)} default positions for school_id {school_id}")
        return True
        
    except Exception as e:
        print(f"Error initializing default positions: {e}")
        db.rollback()
        return False


def get_all_positions(school_id):
    """
    Get all active positions for a school, including positions currently used by staff
    This ensures backward compatibility with legacy position data
    """
    try:
        # Create table if it doesn't exist
        create_positions_table()
        
        db = get_db()
        cursor = db.cursor()
        
        # Get active positions from positions table
        positions = cursor.execute('''
            SELECT id, position_name, description
            FROM positions
            WHERE school_id = ? AND is_active = 1
            ORDER BY position_name
        ''', (school_id,)).fetchall()
        
        # Convert to list of dictionaries
        result = [dict(pos) for pos in positions]
        
        # If no positions exist, initialize defaults
        if not result:
            initialize_default_positions(school_id)
            # Fetch again after initialization
            positions = cursor.execute('''
                SELECT id, position_name, description
                FROM positions
                WHERE school_id = ? AND is_active = 1
                ORDER BY position_name
            ''', (school_id,)).fetchall()
            result = [dict(pos) for pos in positions]
        
        # Get position names that are already in the result
        existing_position_names = {pos['position_name'].lower() for pos in result if pos.get('position_name')}
        
        # Also get positions that are currently being used by staff but not in positions table
        # This handles legacy data and deleted positions
        staff_positions = cursor.execute('''
            SELECT DISTINCT destination as position_name
            FROM staff
            WHERE school_id = ? 
            AND destination IS NOT NULL 
            AND TRIM(destination) != ''
            UNION
            SELECT DISTINCT position as position_name
            FROM staff
            WHERE school_id = ? 
            AND position IS NOT NULL 
            AND TRIM(position) != ''
        ''', (school_id, school_id)).fetchall()
        
        # Add staff positions that aren't already in the result
        for staff_pos in staff_positions:
            pos_name = staff_pos['position_name'].strip() if staff_pos['position_name'] else None
            if pos_name and pos_name.lower() not in existing_position_names:
                result.append({
                    'id': 0,  # Legacy position (not in positions table)
                    'position_name': pos_name,
                    'description': 'Legacy position'
                })
                existing_position_names.add(pos_name.lower())
        
        # Sort the final result by position name
        result.sort(key=lambda x: x['position_name'])
        
        return result
        
    except Exception as e:
        print(f"Error fetching positions: {e}")
        # Return default list if database operation fails
        return [
            {'id': 0, 'position_name': 'Teacher', 'description': ''},
            {'id': 0, 'position_name': 'Principal', 'description': ''},
            {'id': 0, 'position_name': 'Vice Principal', 'description': ''},
            {'id': 0, 'position_name': 'HOD', 'description': ''}
        ]


def add_position(name, description, school_id):
    """Add a new position to the database"""
    db = None
    try:
        if not name or not name.strip():
            return {'success': False, 'message': 'Position name is required'}
        
        name = name.strip()
        
        # Create table if it doesn't exist
        create_positions_table()
        
        db = get_db()
        cursor = db.cursor()
        
        # Check for existing position (both active and inactive)
        existing = cursor.execute('''
            SELECT id, is_active FROM positions 
            WHERE school_id = ? AND LOWER(position_name) = LOWER(?)
        ''', (school_id, name)).fetchone()
        
        if existing:
            # If position exists and is inactive, reactivate it
            if existing['is_active'] == 0:
                cursor.execute('''
                    UPDATE positions 
                    SET is_active = 1, description = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND school_id = ?
                ''', (description or '', existing['id'], school_id))
                
                db.commit()
                
                return {
                    'success': True,
                    'message': f'Position "{name}" reactivated successfully',
                    'position_name': name
                }
            else:
                # Position exists and is active
                return {'success': False, 'message': 'Position already exists'}
        
        # Insert new position if it doesn't exist
        cursor.execute('''
            INSERT INTO positions (school_id, position_name, description)
            VALUES (?, ?, ?)
        ''', (school_id, name, description or ''))
        
        db.commit()
        
        return {
            'success': True,
            'message': f'Position "{name}" added successfully',
            'position_name': name
        }
        
    except Exception as e:
        print(f"Error adding position: {e}")
        if db:
            db.rollback()
        return {'success': False, 'message': f'Error adding position: {str(e)}'}

def delete_position(position_id, school_id):
    """
    Soft delete a position by setting is_active to 0
    
    Args:
        position_id: The ID of the position to delete
        school_id: The school ID (for security)
    
    Returns:
        dict: {'success': bool, 'message': str}
    """
    db = None
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Verify the position belongs to the school
        cursor.execute('''
            SELECT id, position_name FROM positions 
            WHERE id = ? AND school_id = ? AND is_active = 1
        ''', (position_id, school_id))
        
        position = cursor.fetchone()
        
        if not position:
            return {'success': False, 'message': 'Position not found or already deleted'}
        
        position_name = position[1]
        
        # Soft delete the position
        cursor.execute('''
            UPDATE positions 
            SET is_active = 0, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND school_id = ?
        ''', (position_id, school_id))
        
        db.commit()
        
        return {
            'success': True,
            'message': f'Position "{position_name}" deleted successfully'
        }
        
    except Exception as e:
        print(f"Error deleting position: {e}")
        if db:
            db.rollback()
        return {'success': False, 'message': f'Error deleting position: {str(e)}'}


# =============================================================================
# BIOMETRIC DEVICE MANAGEMENT FUNCTIONS
# =============================================================================

def get_device_for_institution(school_id, device_id=None):
    """
    Get biometric device(s) for an institution
    
    Args:
        school_id: The institution ID
        device_id: Optional specific device ID
    
    Returns:
        Device dict or list of devices
    """
    db = get_db()
    cursor = db.cursor()
    
    if device_id:
        # Get specific device
        cursor.execute('''
            SELECT * FROM biometric_devices 
            WHERE id = ? AND school_id = ? AND is_active = 1
        ''', (device_id, school_id))
        row = cursor.fetchone()
        return dict(row) if row else None
    else:
        # Get all active devices for institution
        cursor.execute('''
            SELECT * FROM biometric_devices 
            WHERE school_id = ? AND is_active = 1
            ORDER BY device_name
        ''', (school_id,))
        return [dict(row) for row in cursor.fetchall()]


def get_primary_device_for_institution(school_id):
    """
    Get the first active device for an institution (for backward compatibility)
    
    Args:
        school_id: The institution ID
    
    Returns:
        Device dict or None
    """
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT * FROM biometric_devices 
        WHERE school_id = ? AND is_active = 1
        ORDER BY id
        LIMIT 1
    ''', (school_id,))
    
    row = cursor.fetchone()
    return dict(row) if row else None


def get_all_devices_with_details():
    """
    Get all biometric devices with institution and agent details
    
    Returns:
        List of device dicts with joined data
    """
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT 
            d.id, d.device_name, d.connection_type, d.ip_address, d.port,
            d.serial_number, d.is_active, d.last_sync, d.sync_status,
            s.name as school_name, s.id as school_id,
            a.agent_name, a.id as agent_id, a.is_active as agent_active
        FROM biometric_devices d
        LEFT JOIN schools s ON d.school_id = s.id
        LEFT JOIN biometric_agents a ON d.agent_id = a.id
        ORDER BY d.school_id, d.device_name
    ''')
    
    return [dict(row) for row in cursor.fetchall()]


def create_biometric_device(school_id, device_name, connection_type, ip_address=None, 
                            port=4370, serial_number=None, agent_id=None):
    """
    Create a new biometric device
    
    Args:
        school_id: Institution ID
        device_name: Display name for device
        connection_type: 'Direct_LAN', 'ADMS', or 'Agent_LAN'
        ip_address: IP address (for Direct_LAN or Agent_LAN)
        port: Port number (default 4370)
        serial_number: Serial number (for ADMS)
        agent_id: Local agent ID (for Agent_LAN)
    
    Returns:
        dict: {'success': bool, 'message': str, 'device_id': int}
    """
    db = None
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Validate connection_type
        valid_types = ['Direct_LAN', 'ADMS', 'Agent_LAN']
        if connection_type not in valid_types:
            return {'success': False, 'message': f'Invalid connection type. Must be one of: {", ".join(valid_types)}'}
        
        # Validate required fields based on connection type
        if connection_type == 'Direct_LAN' and not ip_address:
            return {'success': False, 'message': 'IP address is required for Direct LAN connection'}
        
        if connection_type == 'ADMS' and not serial_number:
            return {'success': False, 'message': 'Serial number is required for ADMS connection'}
        
        if connection_type == 'Agent_LAN' and not agent_id:
            return {'success': False, 'message': 'Agent ID is required for Agent LAN connection'}
        
        # Check for duplicate device name in same institution
        cursor.execute('''
            SELECT id FROM biometric_devices 
            WHERE school_id = ? AND device_name = ? AND is_active = 1
        ''', (school_id, device_name))
        
        existing = cursor.fetchone()
        if existing:
            return {
                'success': False, 
                'message': f'Device name "{device_name}" already exists in this institution. Please use a different name (e.g., "{device_name} 2")'
            }
        
        # Insert device
        cursor.execute('''
            INSERT INTO biometric_devices 
            (school_id, device_name, connection_type, ip_address, port, 
             serial_number, agent_id, is_active, sync_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, 'pending')
        ''', (school_id, device_name, connection_type, ip_address, port, serial_number, agent_id))
        
        device_id = cursor.lastrowid
        db.commit()
        
        return {
            'success': True,
            'message': f'Device "{device_name}" created successfully',
            'device_id': device_id
        }
        
    except Exception as e:
        print(f"Error creating biometric device: {e}")
        if db:
            db.rollback()
        return {'success': False, 'message': f'Error creating device: {str(e)}'}


def update_biometric_device(device_id, school_id, device_name=None, ip_address=None, 
                            port=None, serial_number=None, agent_id=None):
    """
    Update biometric device details
    
    Args:
        device_id: Device ID to update
        school_id: Institution ID (for security)
        device_name: New device name (optional)
        ip_address: New IP address (optional)
        port: New port (optional)
        serial_number: New serial number (optional)
        agent_id: New agent ID (optional)
    
    Returns:
        dict: {'success': bool, 'message': str}
    """
    db = None
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Verify device belongs to institution
        cursor.execute('''
            SELECT id FROM biometric_devices 
            WHERE id = ? AND school_id = ? AND is_active = 1
        ''', (device_id, school_id))
        
        if not cursor.fetchone():
            return {'success': False, 'message': 'Device not found or access denied'}
        
        # Check for duplicate device name if updating name
        if device_name is not None:
            cursor.execute('''
                SELECT id FROM biometric_devices 
                WHERE school_id = ? AND device_name = ? AND id != ? AND is_active = 1
            ''', (school_id, device_name, device_id))
            
            if cursor.fetchone():
                return {
                    'success': False, 
                    'message': f'Device name "{device_name}" already exists in this institution. Please use a different name.'
                }
        
        # Build update query dynamically
        updates = []
        params = []
        
        if device_name is not None:
            updates.append('device_name = ?')
            params.append(device_name)
        
        if ip_address is not None:
            updates.append('ip_address = ?')
            params.append(ip_address)
        
        if port is not None:
            updates.append('port = ?')
            params.append(port)
        
        if serial_number is not None:
            updates.append('serial_number = ?')
            params.append(serial_number)
        
        if agent_id is not None:
            updates.append('agent_id = ?')
            params.append(agent_id)
        
        if not updates:
            return {'success': False, 'message': 'No fields to update'}
        
        updates.append('updated_at = CURRENT_TIMESTAMP')
        params.extend([device_id, school_id])
        
        query = f'''
            UPDATE biometric_devices 
            SET {', '.join(updates)}
            WHERE id = ? AND school_id = ?
        '''
        
        cursor.execute(query, params)
        db.commit()
        
        return {
            'success': True,
            'message': 'Device updated successfully'
        }
        
    except Exception as e:
        print(f"Error updating biometric device: {e}")
        if db:
            db.rollback()
        return {'success': False, 'message': f'Error updating device: {str(e)}'}


def delete_biometric_device(device_id, school_id):
    """
    Soft delete a biometric device
    
    Args:
        device_id: Device ID
        school_id: Institution ID (for security)
    
    Returns:
        dict: {'success': bool, 'message': str}
    """
    db = None
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Verify device belongs to institution
        cursor.execute('''
            SELECT device_name FROM biometric_devices 
            WHERE id = ? AND school_id = ? AND is_active = 1
        ''', (device_id, school_id))
        
        device = cursor.fetchone()
        if not device:
            return {'success': False, 'message': 'Device not found or already deleted'}
        
        device_name = device[0]
        
        # Soft delete
        cursor.execute('''
            UPDATE biometric_devices 
            SET is_active = 0, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND school_id = ?
        ''', (device_id, school_id))
        
        db.commit()
        
        return {
            'success': True,
            'message': f'Device "{device_name}" deleted successfully'
        }
        
    except Exception as e:
        print(f"Error deleting biometric device: {e}")
        if db:
            db.rollback()
        return {'success': False, 'message': f'Error deleting device: {str(e)}'}


def update_device_sync_status(device_id, last_sync=None, sync_status='success'):
    """
    Update device sync status and timestamp
    
    Args:
        device_id: Device ID
        last_sync: Last sync datetime (defaults to now in local time)
        sync_status: Sync status ('success', 'failed', 'pending', 'unknown')
    
    Returns:
        bool: Success status
    """
    db = None
    try:
        from datetime import datetime
        db = get_db()
        cursor = db.cursor()
        
        if last_sync is None:
            # Use local time instead of UTC
            last_sync = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            UPDATE biometric_devices 
            SET last_sync = ?, sync_status = ?
            WHERE id = ?
        ''', (last_sync, sync_status, device_id))
        
        db.commit()
        return True
        
    except Exception as e:
        print(f"Error updating device sync status: {e}")
        if db:
            db.rollback()
        return False


# =============================================================================
# BIOMETRIC AGENT MANAGEMENT FUNCTIONS
# =============================================================================

def get_agents_for_institution(school_id):
    """
    Get all agents for an institution
    
    Args:
        school_id: Institution ID
    
    Returns:
        List of agent dicts
    """
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT * FROM biometric_agents 
        WHERE school_id = ? 
        ORDER BY agent_name
    ''', (school_id,))
    
    return [dict(row) for row in cursor.fetchall()]


def get_all_agents_with_details():
    """
    Get all agents with institution details
    
    Returns:
        List of agent dicts with joined data
    """
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT 
            a.id, a.agent_name, a.api_key, a.is_active, 
            a.last_heartbeat, a.created_at,
            s.name as school_name, s.id as school_id,
            COUNT(d.id) as device_count
        FROM biometric_agents a
        LEFT JOIN schools s ON a.school_id = s.id
        LEFT JOIN biometric_devices d ON a.id = d.agent_id AND d.is_active = 1
        GROUP BY a.id
        ORDER BY a.school_id, a.agent_name
    ''')
    
    return [dict(row) for row in cursor.fetchall()]


def create_biometric_agent(school_id, agent_name):
    """
    Create a new local agent
    
    Args:
        school_id: Institution ID
        agent_name: Display name for agent
    
    Returns:
        dict: {'success': bool, 'message': str, 'agent_id': int, 'api_key': str}
    """
    db = None
    try:
        import secrets
        
        db = get_db()
        cursor = db.cursor()
        
        # Generate unique API key
        api_key = secrets.token_urlsafe(48)
        
        # Insert agent
        cursor.execute('''
            INSERT INTO biometric_agents 
            (school_id, agent_name, api_key, is_active)
            VALUES (?, ?, ?, 1)
        ''', (school_id, agent_name, api_key))
        
        agent_id = cursor.lastrowid
        db.commit()
        
        return {
            'success': True,
            'message': f'Agent "{agent_name}" created successfully',
            'agent_id': agent_id,
            'api_key': api_key
        }
        
    except Exception as e:
        print(f"Error creating biometric agent: {e}")
        if db:
            db.rollback()
        return {'success': False, 'message': f'Error creating agent: {str(e)}'}


def update_agent_heartbeat(api_key):
    """
    Update agent last heartbeat timestamp
    
    Args:
        api_key: Agent API key
    
    Returns:
        dict: {'success': bool, 'agent_id': int, 'school_id': int}
    """
    db = None
    try:
        db = get_db()
        import datetime
        cursor = db.cursor()
        
        # Get current UTC timestamp
        current_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        # Get agent info and update heartbeat
        cursor.execute('''
            UPDATE biometric_agents 
            SET last_heartbeat = ?, updated_at = ?
            WHERE api_key = ? AND is_active = 1
        ''', (current_time, current_time, api_key))
        
        if cursor.rowcount == 0:
            return {'success': False, 'message': 'Invalid API key or agent inactive'}
        
        # Get agent details
        cursor.execute('''
            SELECT id, school_id FROM biometric_agents 
            WHERE api_key = ?
        ''', (api_key,))
        
        row = cursor.fetchone()
        db.commit()
        
        return {
            'success': True,
            'agent_id': row[0],
            'school_id': row[1],
            'last_heartbeat': current_time
        }
        
    except Exception as e:
        print(f"Error updating agent heartbeat: {e}")
        if db:
            db.rollback()
        return {'success': False, 'message': f'Error: {str(e)}'}


def verify_agent_api_key(api_key):
    """
    Verify agent API key and return agent/school info
    
    Args:
        api_key: Agent API key
    
    Returns:
        dict: Agent info or None
    """
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT a.id, a.school_id, a.agent_name, a.is_active,
               s.name as school_name
        FROM biometric_agents a
        LEFT JOIN schools s ON a.school_id = s.id
        WHERE a.api_key = ? AND a.is_active = 1
    ''', (api_key,))
    
    row = cursor.fetchone()
    return dict(row) if row else None


def deactivate_biometric_agent(agent_id, school_id):
    """
    Deactivate a local agent
    
    Args:
        agent_id: Agent ID
        school_id: Institution ID (for security)
    
    Returns:
        dict: {'success': bool, 'message': str}
    """
    db = None
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Verify agent belongs to institution
        cursor.execute('''
            SELECT agent_name FROM biometric_agents 
            WHERE id = ? AND school_id = ? AND is_active = 1
        ''', (agent_id, school_id))
        
        agent = cursor.fetchone()
        if not agent:
            return {'success': False, 'message': 'Agent not found or already deactivated'}
        
        agent_name = agent[0]
        
        # Deactivate agent
        cursor.execute('''
            UPDATE biometric_agents 
            SET is_active = 0, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND school_id = ?
        ''', (agent_id, school_id))
        
        db.commit()
        
        return {
            'success': True,
            'message': f'Agent "{agent_name}" deactivated successfully'
        }
        
    except Exception as e:
        print(f"Error deactivating agent: {e}")
        if db:
            db.rollback()
        return {'success': False, 'message': f'Error deactivating agent: {str(e)}'}


def get_all_schools():
    """
    Get list of all schools for dropdown menus
    
    Returns:
        list: List of school dictionaries with id and name
    """
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            SELECT id, name 
            FROM schools 
            ORDER BY name
        ''')
        
        schools = []
        for row in cursor.fetchall():
            schools.append({
                'id': row[0],
                'name': row[1]
            })
        
        return schools
        
    except Exception as e:
        print(f"Error fetching schools: {e}")
        return []


def get_system_setting(key, default_value=None):
    """
    Get a system setting value by key
    
    Args:
        key: Setting key
        default_value: Default value if setting doesn't exist
    
    Returns:
        Setting value or default_value
    """
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            SELECT setting_value FROM system_settings 
            WHERE setting_key = ?
        ''', (key,))
        
        row = cursor.fetchone()
        return row[0] if row else default_value
        
    except Exception as e:
        print(f"Error getting system setting {key}: {e}")
        return default_value


def set_system_setting(key, value, description=None):
    """
    Set a system setting value
    
    Args:
        key: Setting key
        value: Setting value
        description: Optional description
    
    Returns:
        bool: Success status
    """
    db = None
    try:
        import datetime
        db = get_db()
        cursor = db.cursor()
        
        current_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO system_settings (setting_key, setting_value, description, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(setting_key) DO UPDATE SET
                setting_value = excluded.setting_value,
                description = COALESCE(excluded.description, description),
                updated_at = excluded.updated_at
        ''', (key, str(value), description, current_time))
        
        db.commit()
        return True
        
    except Exception as e:
        print(f"Error setting system setting {key}: {e}")
        if db:
            db.rollback()
        return False
