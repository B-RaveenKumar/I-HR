# salary_calculator.py
"""
Comprehensive Salary Calculator for VishnoRex Attendance System

This module calculates salaries based on various attendance factors:
- Present days (full pay)
- Absent days (deductions)
- On duty days (full pay)
- Permission/Leave days (based on leave type)
- Arrived soon bonus (early arrival incentive)
- Left soon deductions (early departure penalty)
- Overtime calculations
- Late arrival penalties
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from database import get_db, calculate_hourly_rate, calculate_standard_working_hours_per_month, is_holiday
import calendar


class SalaryCalculator:
    """Comprehensive salary calculation system"""
    
    def __init__(self, school_id=None):
        self.school_id = school_id
        self._last_salary_rules_error = None
        # Default salary calculation rules (fallback values)
        self.default_salary_rules = {
            'early_arrival_bonus_per_hour': 50.0,  # Bonus for arriving early
            'early_departure_penalty_per_hour': 100.0,  # Penalty for leaving early
            'late_arrival_penalty_per_hour': 75.0,  # Penalty for being late
            'absent_day_deduction_rate': 1.0,  # Full day salary deduction
            'half_day_threshold_hours': 4.0,  # Minimum hours for half day
            'overtime_rate_multiplier': 1.5,  # 1.5x regular rate for overtime
            'on_duty_rate': 1.0,  # Full pay for on duty days
            'permission_deduction_rate': 0.0,  # No deduction for approved permissions
            'sick_leave_rate': 1.0,  # Full pay for sick leave (up to limit)
            'casual_leave_rate': 1.0,  # Full pay for casual leave
            'earned_leave_rate': 1.0,  # Full pay for earned leave
            'maternity_leave_rate': 1.0,  # Full pay for maternity leave
            'unpaid_leave_rate': 0.0,  # No pay for unpaid leave
            'bonus_rate_percentage': 10.0,  # Bonus percentage for extra hours worked
            'minimum_hours_for_bonus': 5.0,  # Minimum extra hours to qualify for bonus
        }
        
        # Load salary rules from database or use defaults
        self.salary_rules = self._load_salary_rules_from_db()

    def _get_db_connection(self):
        """Get database connection with fallback for standalone operation"""
        try:
            # Try Flask's get_db first (when running in Flask context)
            return get_db()
        except RuntimeError:
            # Fallback to direct SQLite connection (for standalone testing)
            import sqlite3
            conn = sqlite3.connect('vishnorex.db', check_same_thread=False)
            conn.row_factory = sqlite3.Row  # This enables dict-like access
            return conn

    @staticmethod
    def _to_float(value, default=0.0):
        """Safely convert DB numeric values (including NULL) to float."""
        try:
            if value is None:
                return float(default)
            return float(value)
        except (TypeError, ValueError):
            return float(default)
    
    @staticmethod
    def _to_date(value):
        """Safely convert DB date values (string or datetime.date) to datetime.date."""
        from datetime import date
        try:
            if value is None:
                return None
            # If already a date object, return it
            if isinstance(value, date):
                return value
            # If it's a string, parse it
            if isinstance(value, str):
                return datetime.strptime(value, '%Y-%m-%d').date()
            return value
        except (TypeError, ValueError):
            return None
    
    def _ensure_salary_rules_table(self):
        """Ensure the salary_rules table exists"""
        try:
            db = self._get_db_connection()
            db.execute('''
                CREATE TABLE IF NOT EXISTS salary_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    school_id INTEGER DEFAULT 0,
                    rule_name TEXT NOT NULL,
                    rule_value REAL NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(school_id, rule_name)
                )
            ''')
            db.commit()
            return True
        except Exception as e:
            print(f"Error creating salary_rules table: {e}")
            return False

    def _get_salary_rules_columns(self, db):
        """Return available columns in salary_rules table (works on SQLite and MySQL wrapper)."""
        try:
            columns_info = db.execute("PRAGMA table_info(salary_rules)").fetchall()
            columns = set()

            for col in columns_info:
                # sqlite3.Row / dict-like access
                if isinstance(col, dict):
                    columns.add(col.get('name'))
                else:
                    try:
                        columns.add(col['name'])
                    except (TypeError, KeyError, IndexError):
                        # tuple-style fallback: (cid, name, type, notnull, dflt_value, pk)
                        if len(col) > 1:
                            columns.add(col[1])

            return {c for c in columns if c}
        except Exception:
            return set()

    def _get_salary_rules_id_insert_mode(self, db):
        """Determine whether salary_rules.id can be omitted during INSERT.

        Returns:
            'omit_id' when id is auto-generated or absent
            'explicit_id' when id exists but requires explicit value
        """
        try:
            columns = self._get_salary_rules_columns(db)
            if 'id' not in columns:
                return 'omit_id'

            # MySQL path: inspect INFORMATION_SCHEMA for AUTO_INCREMENT.
            row = db.execute('''
                SELECT EXTRA
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'salary_rules'
                  AND COLUMN_NAME = 'id'
                LIMIT 1
            ''').fetchone()

            if row:
                extra = row['EXTRA'] if isinstance(row, dict) else row[0]
                if extra and 'auto_increment' in str(extra).lower():
                    return 'omit_id'
                return 'explicit_id'

            return 'omit_id'
        except Exception:
            # SQLite or unavailable metadata: assume normal autoincrement behavior.
            return 'omit_id'

    def _get_next_salary_rule_id(self, db):
        """Return next numeric id for legacy salary_rules tables without AUTO_INCREMENT."""
        row = db.execute('SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM salary_rules').fetchone()
        if isinstance(row, dict):
            return int(row.get('next_id', 1))
        try:
            return int(row['next_id'])
        except Exception:
            return int(row[0])
    
    def _load_salary_rules_from_db(self):
        """Load salary rules from database or return defaults"""
        try:
            # Ensure table exists
            if not self._ensure_salary_rules_table():
                return self.default_salary_rules.copy()
            
            db = self._get_db_connection()
            columns = self._get_salary_rules_columns(db)
            has_school_id = 'school_id' in columns
            
            # Use school_id = 0 for global rules if no specific school_id
            search_school_id = self.school_id if self.school_id is not None else 0

            # Load rules with compatibility for legacy schemas.
            if has_school_id:
                rules = db.execute('''
                    SELECT rule_name, rule_value
                    FROM salary_rules
                    WHERE school_id = ?
                ''', (search_school_id,)).fetchall()
            else:
                rules = db.execute('''
                    SELECT rule_name, rule_value
                    FROM salary_rules
                ''').fetchall()
            
            # Start with defaults and update with database values
            loaded_rules = self.default_salary_rules.copy()
            for rule in rules:
                loaded_rules[rule['rule_name']] = rule['rule_value']
            
            return loaded_rules
            
        except Exception as e:
            print(f"Error loading salary rules from database: {e}")
            return self.default_salary_rules.copy()
    
    def _save_salary_rules_to_db(self, rules_to_save):
        """Save salary rules to database"""
        try:
            self._last_salary_rules_error = None
            # Ensure table exists
            if not self._ensure_salary_rules_table():
                return False
            
            db = self._get_db_connection()
            columns = self._get_salary_rules_columns(db)
            has_school_id = 'school_id' in columns
            has_updated_at = 'updated_at' in columns
            id_insert_mode = self._get_salary_rules_id_insert_mode(db)
            
            # Use school_id = 0 for global rules if no specific school_id
            save_school_id = self.school_id if self.school_id is not None else 0

            for rule_name, rule_value in rules_to_save.items():
                if has_school_id:
                    existing = db.execute('''
                        SELECT 1
                        FROM salary_rules
                        WHERE school_id = ? AND rule_name = ?
                        LIMIT 1
                    ''', (save_school_id, rule_name)).fetchone()

                    if existing:
                        if has_updated_at:
                            db.execute('''
                                UPDATE salary_rules
                                SET rule_value = ?, updated_at = CURRENT_TIMESTAMP
                                WHERE school_id = ? AND rule_name = ?
                            ''', (rule_value, save_school_id, rule_name))
                        else:
                            db.execute('''
                                UPDATE salary_rules
                                SET rule_value = ?
                                WHERE school_id = ? AND rule_name = ?
                            ''', (rule_value, save_school_id, rule_name))
                    else:
                        if has_updated_at:
                            if id_insert_mode == 'explicit_id':
                                next_id = self._get_next_salary_rule_id(db)
                                db.execute('''
                                    INSERT INTO salary_rules
                                    (id, school_id, rule_name, rule_value, updated_at)
                                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                                ''', (next_id, save_school_id, rule_name, rule_value))
                            else:
                                db.execute('''
                                    INSERT INTO salary_rules
                                    (school_id, rule_name, rule_value, updated_at)
                                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                                ''', (save_school_id, rule_name, rule_value))
                        else:
                            if id_insert_mode == 'explicit_id':
                                next_id = self._get_next_salary_rule_id(db)
                                db.execute('''
                                    INSERT INTO salary_rules
                                    (id, school_id, rule_name, rule_value)
                                    VALUES (?, ?, ?, ?)
                                ''', (next_id, save_school_id, rule_name, rule_value))
                            else:
                                db.execute('''
                                    INSERT INTO salary_rules
                                    (school_id, rule_name, rule_value)
                                    VALUES (?, ?, ?)
                                ''', (save_school_id, rule_name, rule_value))
                else:
                    existing = db.execute('''
                        SELECT 1
                        FROM salary_rules
                        WHERE rule_name = ?
                        LIMIT 1
                    ''', (rule_name,)).fetchone()

                    if existing:
                        if has_updated_at:
                            db.execute('''
                                UPDATE salary_rules
                                SET rule_value = ?, updated_at = CURRENT_TIMESTAMP
                                WHERE rule_name = ?
                            ''', (rule_value, rule_name))
                        else:
                            db.execute('''
                                UPDATE salary_rules
                                SET rule_value = ?
                                WHERE rule_name = ?
                            ''', (rule_value, rule_name))
                    else:
                        if has_updated_at:
                            if id_insert_mode == 'explicit_id':
                                next_id = self._get_next_salary_rule_id(db)
                                db.execute('''
                                    INSERT INTO salary_rules
                                    (id, rule_name, rule_value, updated_at)
                                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                                ''', (next_id, rule_name, rule_value))
                            else:
                                db.execute('''
                                    INSERT INTO salary_rules
                                    (rule_name, rule_value, updated_at)
                                    VALUES (?, ?, CURRENT_TIMESTAMP)
                                ''', (rule_name, rule_value))
                        else:
                            if id_insert_mode == 'explicit_id':
                                next_id = self._get_next_salary_rule_id(db)
                                db.execute('''
                                    INSERT INTO salary_rules
                                    (id, rule_name, rule_value)
                                    VALUES (?, ?, ?)
                                ''', (next_id, rule_name, rule_value))
                            else:
                                db.execute('''
                                    INSERT INTO salary_rules
                                    (rule_name, rule_value)
                                    VALUES (?, ?)
                                ''', (rule_name, rule_value))
            
            db.commit()
            return True
            
        except Exception as e:
            self._last_salary_rules_error = str(e)
            print(f"Error saving salary rules to database: {e}")
            return False

    def calculate_monthly_salary(self, staff_id: int, year: int, month: int) -> Dict:
        """Calculate comprehensive monthly salary for a staff member"""
        try:
            # Get staff details
            staff_info = self._get_staff_info(staff_id)
            if not staff_info:
                return {'success': False, 'error': 'Staff not found'}
            
            # Get attendance data for the month
            attendance_data = self._get_monthly_attendance(staff_id, year, month)
            
            # Get leave data for the month
            leave_data = self._get_monthly_leaves(staff_id, year, month)
            
            # Get permission data for the month
            permission_data = self._get_monthly_permissions(staff_id, year, month)
            
            # Calculate working days in month (excluding holidays)  
            # Get staff department for department-specific holidays
            staff_department = staff_info.get('department')
            working_days = self._get_working_days_excluding_holidays(year, month, staff_department)
            
            # Perform salary calculations
            salary_breakdown = self._calculate_salary_breakdown(
                staff_info, attendance_data, leave_data, permission_data, working_days, year, month
            )
            
            return {
                'success': True,
                'staff_info': staff_info,
                'salary_breakdown': salary_breakdown,
                'calculation_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def calculate_enhanced_monthly_salary(self, staff_id: int, year: int, month: int) -> Dict:
        """
        Calculate enhanced monthly salary based on actual hours worked vs standard hours.
        Includes bonus for extra hours and proportional reduction for fewer hours.
        """
        try:
            # Get staff details
            staff_info = self._get_staff_info(staff_id)
            if not staff_info:
                return {'success': False, 'error': 'Staff not found'}

            # Get base monthly salary
            base_monthly_salary = self._to_float(staff_info.get('basic_salary', 0))
            if base_monthly_salary <= 0:
                return {'success': False, 'error': 'Base monthly salary not set for this staff member'}

            # Calculate hourly rate using institution timing configuration
            hourly_rate_info = calculate_hourly_rate(base_monthly_salary)
            hourly_rate = hourly_rate_info['hourly_rate']
            standard_monthly_hours = hourly_rate_info['standard_monthly_hours']

            # Get attendance data for the month
            attendance_data = self._get_monthly_attendance(staff_id, year, month)

            # Calculate actual hours worked
            actual_hours_worked = self._calculate_actual_hours_worked(attendance_data)

            # Get leave data for the month
            leave_data = self._get_monthly_leaves(staff_id, year, month)

            # Get permission data for the month
            permission_data = self._get_monthly_permissions(staff_id, year, month)

            # Calculate working days in month (excluding holidays)
            # Get staff department for department-specific holidays
            staff_department = staff_info.get('department')
            working_days = self._get_working_days_excluding_holidays(year, month, staff_department)

            # Perform enhanced salary calculations
            salary_breakdown = self._calculate_enhanced_salary_breakdown(
                staff_info, attendance_data, leave_data, permission_data, working_days,
                actual_hours_worked, standard_monthly_hours, hourly_rate, year, month
            )

            return {
                'success': True,
                'staff_id': staff_id,
                'staff_name': staff_info.get('full_name', 'Unknown'),
                'calculation_period': f"{year}-{month:02d}",
                'base_monthly_salary': base_monthly_salary,
                'hourly_rate': hourly_rate,
                'standard_monthly_hours': standard_monthly_hours,
                'actual_hours_worked': actual_hours_worked,
                'salary_breakdown': salary_breakdown
            }

        except Exception as e:
            return {'success': False, 'error': f'Error calculating enhanced salary: {str(e)}'}

    def _calculate_actual_hours_worked(self, attendance_data: List[Dict]) -> float:
        """Calculate total actual hours worked from attendance data"""
        total_hours = 0.0

        for record in attendance_data:
            if record['status'] in ['present', 'late', 'left_soon']:
                # Use work_hours if available, otherwise calculate from time_in and time_out
                if record.get('work_hours') and record['work_hours'] > 0:
                    total_hours += float(record['work_hours'])
                elif record.get('time_in') and record.get('time_out'):
                    try:
                        time_in = datetime.strptime(record['time_in'], '%H:%M:%S').time()
                        time_out = datetime.strptime(record['time_out'], '%H:%M:%S').time()

                        # Calculate hours worked
                        time_in_dt = datetime.combine(datetime.today(), time_in)
                        time_out_dt = datetime.combine(datetime.today(), time_out)

                        # Handle overnight shifts
                        if time_out_dt < time_in_dt:
                            time_out_dt += timedelta(days=1)

                        hours_worked = (time_out_dt - time_in_dt).total_seconds() / 3600
                        total_hours += hours_worked
                    except:
                        # If time parsing fails, use standard daily hours
                        standard_hours = calculate_standard_working_hours_per_month()
                        total_hours += standard_hours['daily_hours']

            elif record['status'] == 'on_duty':
                # On duty days count as full working hours
                standard_hours = calculate_standard_working_hours_per_month()
                total_hours += standard_hours['daily_hours']

        return round(total_hours, 2)

    def _calculate_enhanced_salary_breakdown(self, staff_info: Dict, attendance_data: List[Dict],
                                           leave_data: List[Dict], permission_data: List[Dict], working_days: int,
                                           actual_hours_worked: float, standard_monthly_hours: float,
                                           hourly_rate: float, year: int, month: int) -> Dict:
        """Calculate enhanced salary breakdown with hours-based logic"""

        # Basic salary components
        basic_salary = self._to_float(staff_info.get('basic_salary', 0))
        hra = self._to_float(staff_info.get('hra', 0))
        transport_allowance = self._to_float(staff_info.get('transport_allowance', 0))
        other_allowances = self._to_float(staff_info.get('other_allowances', 0))

        # Calculate gross salary
        gross_salary = basic_salary + hra + transport_allowance + other_allowances

        # Calculate salary based on actual hours worked
        if standard_monthly_hours > 0:
            hours_ratio = actual_hours_worked / standard_monthly_hours
            base_salary_earned = basic_salary * hours_ratio
        else:
            hours_ratio = 1.0
            base_salary_earned = basic_salary

        # Calculate bonus for extra hours worked
        extra_hours = max(0, actual_hours_worked - standard_monthly_hours)
        bonus_amount = 0.0

        if extra_hours >= self.salary_rules['minimum_hours_for_bonus']:
            bonus_rate = self.salary_rules['bonus_rate_percentage'] / 100
            bonus_amount = extra_hours * hourly_rate * bonus_rate

        # Calculate other earnings and deductions (existing logic)
        early_arrival_bonus = 0.0
        early_departure_penalty = 0.0
        late_arrival_penalty = 0.0
        overtime_pay = 0.0

        # Process attendance records for bonuses/penalties
        for record in attendance_data:
            if record['status'] in ['present', 'late', 'left_soon']:
                # Calculate early arrival bonus
                if record.get('early_arrival_minutes') and record['early_arrival_minutes'] > 0:
                    early_hours = record['early_arrival_minutes'] / 60
                    early_arrival_bonus += early_hours * self.salary_rules['early_arrival_bonus_per_hour']

                # Calculate early departure penalty
                if record.get('early_departure_minutes') and record['early_departure_minutes'] > 0:
                    # Check if there's an approved permission for this date
                    has_permission = any(p['permission_date'] == record['date'] for p in permission_data)
                    if not has_permission:
                        early_dep_hours = record['early_departure_minutes'] / 60
                        early_departure_penalty += early_dep_hours * self.salary_rules['early_departure_penalty_per_hour']

                # Calculate late arrival penalty
                if record.get('late_duration_minutes') and record['late_duration_minutes'] > 0:
                    late_hours = record['late_duration_minutes'] / 60
                    late_arrival_penalty += late_hours * self.salary_rules['late_arrival_penalty_per_hour']

                # Calculate overtime pay
                if record.get('overtime_hours') and record['overtime_hours'] > 0:
                    overtime_pay += record['overtime_hours'] * hourly_rate * self.salary_rules['overtime_rate_multiplier']

        # Calculate leave pay (using existing leave processing logic)
        leave_summary = self._process_leave_data(leave_data, hourly_rate * 8, year, month)  # 8 hours per day
        leave_pay = leave_summary['leave_pay']

        # Calculate deductions
        pf_deduction = self._to_float(staff_info.get('pf_deduction', 0))
        esi_deduction = self._to_float(staff_info.get('esi_deduction', 0))
        professional_tax = self._to_float(staff_info.get('professional_tax', 0))
        other_deductions = self._to_float(staff_info.get('other_deductions', 0))

        # Total earnings
        total_earnings = (
            base_salary_earned +
            hra +
            transport_allowance +
            other_allowances +
            bonus_amount +
            early_arrival_bonus +
            overtime_pay +
            leave_pay
        )

        # Total deductions
        total_deductions = (
            pf_deduction +
            esi_deduction +
            professional_tax +
            other_deductions +
            early_departure_penalty +
            late_arrival_penalty
        )

        # Net salary
        net_salary = total_earnings - total_deductions

        return {
            'base_salary_earned': round(base_salary_earned, 2),
            'hra': round(hra, 2),
            'transport_allowance': round(transport_allowance, 2),
            'other_allowances': round(other_allowances, 2),
            'bonus_for_extra_hours': round(bonus_amount, 2),
            'extra_hours_worked': round(extra_hours, 2),
            'early_arrival_bonus': round(early_arrival_bonus, 2),
            'overtime_pay': round(overtime_pay, 2),
            'leave_pay': round(leave_pay, 2),
            'total_earnings': round(total_earnings, 2),
            'pf_deduction': round(pf_deduction, 2),
            'esi_deduction': round(esi_deduction, 2),
            'professional_tax': round(professional_tax, 2),
            'other_deductions': round(other_deductions, 2),
            'early_departure_penalty': round(early_departure_penalty, 2),
            'late_arrival_penalty': round(late_arrival_penalty, 2),
            'total_deductions': round(total_deductions, 2),
            'net_salary': round(net_salary, 2),
            'hours_ratio': round(hours_ratio, 4) if standard_monthly_hours > 0 else 1.0
        }

    def _get_staff_info(self, staff_id: int) -> Optional[Dict]:
        """Get staff information including salary details"""
        db = self._get_db_connection()
        staff_columns = [col['name'] for col in db.execute("PRAGMA table_info(staff)").fetchall()]
        active_filter = ''
        if 'is_active' in staff_columns:
            active_filter = ' AND COALESCE(s.is_active, 1) = 1'
        elif 'status' in staff_columns:
            active_filter = " AND LOWER(COALESCE(s.status, 'active')) = 'active'"

        staff = db.execute(f'''
            SELECT s.*, 
                   sc.name as school_name,
                   s.basic_salary,
                   s.hra,
                   s.transport_allowance,
                   s.other_allowances,
                   s.pf_deduction,
                   s.esi_deduction,
                   s.professional_tax,
                   s.other_deductions
            FROM staff s
            LEFT JOIN schools sc ON s.school_id = sc.id
            WHERE s.id = ?{active_filter}
        ''', (staff_id,)).fetchone()
        
        if staff:
            return dict(staff)
        return None
    
    def _get_monthly_attendance(self, staff_id: int, year: int, month: int) -> List[Dict]:
        """Get detailed attendance data for the month"""
        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]}"

        db = self._get_db_connection()
        attendance = db.execute('''
            SELECT date, status, time_in, time_out,
                   late_duration_minutes, early_departure_minutes,
                   shift_type, shift_start_time, shift_end_time,
                   overtime_in, overtime_out, on_duty_type, on_duty_location,
                   on_duty_purpose
            FROM attendance
            WHERE staff_id = ? AND date BETWEEN ? AND ?
            ORDER BY date
        ''', (staff_id, start_date, end_date)).fetchall()
        
        return [dict(row) for row in attendance]
    
    def _get_monthly_leaves(self, staff_id: int, year: int, month: int) -> List[Dict]:
        """Get leave applications for the month"""
        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]}"

        db = self._get_db_connection()
        leaves = db.execute('''
            SELECT leave_type, start_date, end_date, status, reason
            FROM leave_applications
            WHERE staff_id = ? AND status = 'approved'
            AND ((start_date BETWEEN ? AND ?) OR (end_date BETWEEN ? AND ?)
                 OR (start_date <= ? AND end_date >= ?))
            ORDER BY start_date
        ''', (staff_id, start_date, end_date, start_date, end_date, start_date, end_date)).fetchall()
        
        return [dict(row) for row in leaves]
    
    def _get_monthly_permissions(self, staff_id: int, year: int, month: int) -> List[Dict]:
        """Get approved permission applications for the month"""
        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]}"

        db = self._get_db_connection()
        permissions = db.execute('''
            SELECT permission_type, permission_date, start_time, end_time, duration_hours, reason, status
            FROM permission_applications
            WHERE staff_id = ? AND status = 'approved'
            AND permission_date BETWEEN ? AND ?
            ORDER BY permission_date
        ''', (staff_id, start_date, end_date)).fetchall()
        
        return [dict(row) for row in permissions]
    
    def _get_working_days_in_month(self, year: int, month: int) -> int:
        """Calculate working days in month (excluding weekends)"""
        total_days = calendar.monthrange(year, month)[1]
        working_days = 0
        
        for day in range(1, total_days + 1):
            date_obj = datetime(year, month, day)
            # Exclude Sundays (weekday 6)
            if date_obj.weekday() != 6:
                working_days += 1
        
        return working_days
    
    def _get_working_days_excluding_holidays(self, year: int, month: int, department: Optional[str] = None) -> int:
        """
        Calculate working days in month excluding weekends AND holidays.
        
        Args:
            year (int): Year
            month (int): Month
            department (str, optional): Department name for department-specific holidays
            
        Returns:
            int: Number of working days excluding holidays
        """
        total_days = calendar.monthrange(year, month)[1]
        working_days = 0
        
        for day in range(1, total_days + 1):
            date_obj = datetime(year, month, day).date()
            
            # Exclude Sundays (weekday 6)
            if datetime(year, month, day).weekday() == 6:
                continue
                
            # Exclude holidays (both institution-wide and department-specific)
            if is_holiday(date_obj, department=department, school_id=self.school_id):
                continue
                
            working_days += 1
        
        return working_days
    
    def _get_holiday_details(self, year: int, month: int, department: Optional[str] = None) -> Dict:
        """
        Get detailed holiday information for the month.
        
        Args:
            year (int): Year
            month (int): Month
            department (str, optional): Department name for department-specific holidays
            
        Returns:
            Dict: Holiday details including count and list
        """
        import json
        
        total_days = calendar.monthrange(year, month)[1]
        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month:02d}-{total_days:02d}"
        
        db = self._get_db_connection()
        
        # Get institution-wide holidays
        institution_holidays = db.execute('''
            SELECT holiday_name, start_date, end_date, holiday_type
            FROM holidays
            WHERE school_id = ?
            AND holiday_type = 'institution_wide'
            AND is_active = 1
            AND (
                (start_date <= ? AND end_date >= ?) OR
                (start_date >= ? AND start_date <= ?) OR
                (end_date >= ? AND end_date <= ?)
            )
            ORDER BY start_date
        ''', (self.school_id, start_date, start_date, start_date, end_date, start_date, end_date)).fetchall()
        
        # Get department-specific holidays if department is provided
        dept_holidays = []
        if department:
            dept_holiday_records = db.execute('''
                SELECT holiday_name, start_date, end_date, holiday_type, departments
                FROM holidays
                WHERE school_id = ?
                AND holiday_type = 'department_specific'
                AND is_active = 1
                AND (
                    (start_date <= ? AND end_date >= ?) OR
                    (start_date >= ? AND start_date <= ?) OR
                    (end_date >= ? AND end_date <= ?)
                )
                ORDER BY start_date
            ''', (self.school_id, start_date, start_date, start_date, end_date, start_date, end_date)).fetchall()
            
            for holiday in dept_holiday_records:
                if holiday['departments']:
                    try:
                        departments = json.loads(holiday['departments'])
                        if department in departments:
                            dept_holidays.append(holiday)
                    except (json.JSONDecodeError, TypeError):
                        continue
        
        # Count total holiday days in the month
        holiday_days = 0
        holiday_list = []
        
        for holiday in institution_holidays:
            h_start = self._to_date(holiday['start_date'])
            h_end = self._to_date(holiday['end_date'])
            
            # Count days within the month
            month_start = datetime(year, month, 1).date()
            month_end = datetime(year, month, total_days).date()
            
            actual_start = max(h_start, month_start)
            actual_end = min(h_end, month_end)
            
            if actual_start <= actual_end:
                days_in_month = (actual_end - actual_start).days + 1
                # Exclude Sundays from holiday count
                for day_offset in range(days_in_month):
                    check_date = actual_start + timedelta(days=day_offset)
                    if check_date.weekday() != 6:  # Not Sunday
                        holiday_days += 1
                
                holiday_list.append({
                    'name': holiday['holiday_name'],
                    'type': 'Institution-wide',
                    'start_date': holiday['start_date'],
                    'end_date': holiday['end_date']
                })
        
        for holiday in dept_holidays:
            h_start = self._to_date(holiday['start_date'])
            h_end = self._to_date(holiday['end_date'])
            
            # Count days within the month
            month_start = datetime(year, month, 1).date()
            month_end = datetime(year, month, total_days).date()
            
            actual_start = max(h_start, month_start)
            actual_end = min(h_end, month_end)
            
            if actual_start <= actual_end:
                days_in_month = (actual_end - actual_start).days + 1
                # Exclude Sundays from holiday count
                for day_offset in range(days_in_month):
                    check_date = actual_start + timedelta(days=day_offset)
                    if check_date.weekday() != 6:  # Not Sunday
                        holiday_days += 1
                
                holiday_list.append({
                    'name': holiday['holiday_name'],
                    'type': f'Department ({department})',
                    'start_date': holiday['start_date'],
                    'end_date': holiday['end_date']
                })
        
        return {
            'holiday_days': holiday_days,
            'holiday_list': holiday_list,
            'institution_holidays': len(institution_holidays),
            'department_holidays': len(dept_holidays)
        }
    
    def _calculate_salary_breakdown(self, staff_info: Dict, attendance_data: List[Dict], 
                                  leave_data: List[Dict], permission_data: List[Dict], working_days: int, 
                                  year: int, month: int) -> Dict:
        """Calculate detailed salary breakdown"""
        
        # Basic salary components
        basic_salary = self._to_float(staff_info.get('basic_salary', 0))
        hra = self._to_float(staff_info.get('hra', 0))
        transport_allowance = self._to_float(staff_info.get('transport_allowance', 0))
        other_allowances = self._to_float(staff_info.get('other_allowances', 0))
        
        # Calculate per-day salary
        gross_salary = basic_salary + hra + transport_allowance + other_allowances
        per_day_salary = gross_salary / working_days if working_days > 0 else 0
        per_hour_salary = per_day_salary / 8  # Assuming 8-hour work day
        
        # Initialize counters
        present_days = 0
        absent_days = 0
        on_duty_days = 0
        leave_days = 0
        half_days = 0
        
        # Bonus and penalty calculations
        early_arrival_bonus = 0.0
        early_departure_penalty = 0.0
        late_arrival_penalty = 0.0
        overtime_pay = 0.0
        
        # Process attendance data
        attendance_summary = self._process_attendance_data(
            attendance_data, per_hour_salary, staff_info, permission_data
        )
        
        present_days = attendance_summary['present_days']
        # absent_days from records is just explicitly marked absent days
        marked_absent_days = attendance_summary['absent_days']
        on_duty_days = attendance_summary['on_duty_days']
        early_arrival_bonus = attendance_summary['early_arrival_bonus']
        early_departure_penalty = attendance_summary['early_departure_penalty']
        late_arrival_penalty = attendance_summary['late_arrival_penalty']
        overtime_pay = attendance_summary['overtime_pay']
        
        # Process leave data
        leave_summary = self._process_leave_data(leave_data, per_day_salary, year, month)
        leave_days = leave_summary['total_leave_days']
        leave_pay = leave_summary['leave_pay']
        
        # Get holiday information
        holiday_details = self._get_holiday_details(year, month, staff_info.get('department'))
        
        # Calculate actual absent days: total working days minus accounted days
        # Since late days are counted as present days, this formula works correctly
        # Note: working_days already excludes holidays, so holidays won't be counted as absent
        absent_days = working_days - present_days - on_duty_days - leave_days
        
        # Calculate final amounts
        present_pay = present_days * per_day_salary
        on_duty_pay = on_duty_days * per_day_salary * self.salary_rules['on_duty_rate']
        absent_deduction = absent_days * per_day_salary * self.salary_rules['absent_day_deduction_rate']
        
        # Total earnings
        total_earnings = (
            present_pay + 
            on_duty_pay + 
            leave_pay + 
            early_arrival_bonus + 
            overtime_pay
        )
        
        # Total deductions
        pf_deduction = self._to_float(staff_info.get('pf_deduction', 0))
        esi_deduction = self._to_float(staff_info.get('esi_deduction', 0))
        professional_tax = self._to_float(staff_info.get('professional_tax', 0))
        other_deductions = self._to_float(staff_info.get('other_deductions', 0))
        
        total_deductions = (
            absent_deduction +
            early_departure_penalty +
            late_arrival_penalty +
            pf_deduction +
            esi_deduction +
            professional_tax +
            other_deductions
        )
        
        # Net salary
        net_salary = total_earnings - total_deductions
        
        return {
            'calculation_period': f"{calendar.month_name[month]} {year}",
            'working_days': working_days,
            'per_day_salary': round(per_day_salary, 2),
            'per_hour_salary': round(per_hour_salary, 2),
            
            # Attendance summary
            'attendance_summary': {
                'present_days': present_days,
                'absent_days': absent_days,
                'on_duty_days': on_duty_days,
                'leave_days': leave_days,
                'half_days': half_days,
                'holiday_days': holiday_details['holiday_days'],
                'holiday_list': holiday_details['holiday_list'],
                'institution_holidays': holiday_details['institution_holidays'],
                'department_holidays': holiday_details['department_holidays']
            },
            
            # Earnings breakdown
            'earnings': {
                'basic_salary': basic_salary,
                'hra': hra,
                'transport_allowance': transport_allowance,
                'other_allowances': other_allowances,
                'present_pay': round(present_pay, 2),
                'on_duty_pay': round(on_duty_pay, 2),
                'leave_pay': round(leave_pay, 2),
                'early_arrival_bonus': round(early_arrival_bonus, 2),
                'overtime_pay': round(overtime_pay, 2),
                'total_earnings': round(total_earnings, 2)
            },
            
            # Deductions breakdown
            'deductions': {
                'absent_deduction': round(absent_deduction, 2),
                'early_departure_penalty': round(early_departure_penalty, 2),
                'late_arrival_penalty': round(late_arrival_penalty, 2),
                'pf_deduction': pf_deduction,
                'esi_deduction': esi_deduction,
                'professional_tax': professional_tax,
                'other_deductions': other_deductions,
                'total_deductions': round(total_deductions, 2)
            },
            
            # Final calculation
            'net_salary': round(net_salary, 2),
            'salary_rules_applied': self.salary_rules
        }
    
    def _process_attendance_data(self, attendance_data: List[Dict], 
                               per_hour_salary: float, staff_info: Dict,
                               permission_data: List[Dict]) -> Dict:
        """Process attendance data for salary calculations"""
        present_days = 0
        absent_days = 0
        on_duty_days = 0
        early_arrival_bonus = 0.0
        early_departure_penalty = 0.0
        late_arrival_penalty = 0.0
        overtime_pay = 0.0
        
        # Preload shift context for date-wise resolution.
        shift_info = self._get_staff_shift_info(staff_info['id'])
        shift_history = self._get_shift_history(staff_info['id'])
        shift_defs = self._get_shift_definitions_map()

        permission_dates = set()
        for p in permission_data:
            p_date = self._to_date(p.get('permission_date'))
            if p_date:
                permission_dates.add(p_date)
        
        for record in attendance_data:
            # Only process working days (exclude Sundays) for salary calculations
            record_day = self._to_date(record.get('date'))
            if not record_day:
                continue
            record_date = datetime.combine(record_day, datetime.min.time())
            if record_date.weekday() == 6:  # Skip Sunday records
                continue

            effective_shift = self._resolve_shift_for_date(
                staff_id=staff_info['id'],
                record=record,
                shift_history=shift_history,
                shift_defs=shift_defs,
                default_shift=shift_info
            )
                
            if record['status'] in ['present', 'late', 'left_soon']:  # Count worked-day statuses as present days
                present_days += 1
                
                # Calculate early arrival bonus
                if record['time_in'] and effective_shift:
                    early_minutes = self._calculate_early_arrival_minutes(
                        record['time_in'], effective_shift['start_time']
                    )
                    if early_minutes > 0:
                        early_hours = early_minutes / 60
                        early_arrival_bonus += early_hours * self.salary_rules['early_arrival_bonus_per_hour']
                
                # Calculate early departure penalty
                if record['time_out'] and effective_shift:
                    early_departure_minutes = self._calculate_early_departure_minutes(
                        record['time_out'], effective_shift['end_time'], effective_shift['start_time']
                    )
                    if early_departure_minutes > 0:
                        has_permission = record_day in permission_dates
                        if not has_permission:
                            early_hours = early_departure_minutes / 60
                            early_departure_penalty += early_hours * self.salary_rules['early_departure_penalty_per_hour']
                
                # Calculate late arrival penalty
                if record['late_duration_minutes'] and record['late_duration_minutes'] > 0:
                    late_hours = record['late_duration_minutes'] / 60
                    late_arrival_penalty += late_hours * self.salary_rules['late_arrival_penalty_per_hour']
                
                # Calculate overtime pay
                overtime_hours = self._calculate_overtime_hours(record['overtime_in'], record['overtime_out'])
                if overtime_hours > 0:
                    overtime_pay += overtime_hours * per_hour_salary * self.salary_rules['overtime_rate_multiplier']
                    
            elif record['status'] == 'on_duty':
                on_duty_days += 1
                
            elif record['status'] == 'absent':
                absent_days += 1
        
        return {
            'present_days': present_days,
            'absent_days': absent_days,
            'on_duty_days': on_duty_days,
            'early_arrival_bonus': early_arrival_bonus,
            'early_departure_penalty': early_departure_penalty,
            'late_arrival_penalty': late_arrival_penalty,
            'overtime_pay': overtime_pay
        }

    def _get_shift_history(self, staff_id: int) -> List[Dict]:
        """Load shift history records for a staff member ordered by effective date."""
        db = self._get_db_connection()
        try:
            # Support legacy schemas that might not have school_id in history table.
            history_cols = [col['name'] for col in db.execute("PRAGMA table_info(staff_shift_history)").fetchall()]
            if 'school_id' in history_cols and self.school_id is not None:
                rows = db.execute('''
                    SELECT shift_type, effective_from, effective_to
                    FROM staff_shift_history
                    WHERE staff_id = ? AND school_id = ?
                    ORDER BY effective_from ASC
                ''', (staff_id, self.school_id)).fetchall()
            else:
                rows = db.execute('''
                    SELECT shift_type, effective_from, effective_to
                    FROM staff_shift_history
                    WHERE staff_id = ?
                    ORDER BY effective_from ASC
                ''', (staff_id,)).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []

    def _get_shift_definitions_map(self) -> Dict[str, Dict]:
        """Return active shift definitions indexed by shift_type."""
        db = self._get_db_connection()
        try:
            rows = db.execute('''
                SELECT shift_type, start_time, end_time, grace_period_minutes
                FROM shift_definitions
                WHERE is_active = 1
            ''').fetchall()
            return {r['shift_type']: dict(r) for r in rows}
        except Exception:
            return {}

    def _get_shift_type_from_history(self, record_date, shift_history: List[Dict]) -> Optional[str]:
        """Resolve effective shift type for a date using staff_shift_history."""
        for row in reversed(shift_history):
            start = self._to_date(row.get('effective_from'))
            end = self._to_date(row.get('effective_to'))
            if not start:
                continue
            if record_date >= start and (end is None or record_date <= end):
                return row.get('shift_type')
        return None

    def _resolve_shift_for_date(self, staff_id: int, record: Dict,
                                shift_history: List[Dict], shift_defs: Dict[str, Dict],
                                default_shift: Dict) -> Dict:
        """Resolve effective shift for attendance date.

        Priority:
        1) Attendance snapshot (shift_start_time/shift_end_time, optional shift_type)
        2) staff_shift_history by date
        3) Current staff shift fallback
        """
        # 1) Attendance snapshot is most reliable for payroll back-calculation.
        if record.get('shift_start_time') and record.get('shift_end_time'):
            snapshot_type = record.get('shift_type') or default_shift.get('shift_type')
            return {
                'shift_type': snapshot_type,
                'start_time': record.get('shift_start_time'),
                'end_time': record.get('shift_end_time'),
                'grace_period_minutes': default_shift.get('grace_period_minutes', 10)
            }

        # 2) Resolve by history for this date.
        record_date = self._to_date(record.get('date'))
        if record_date:
            hist_shift_type = self._get_shift_type_from_history(record_date, shift_history)
            if hist_shift_type and hist_shift_type in shift_defs:
                hist_shift = shift_defs[hist_shift_type]
                return {
                    'shift_type': hist_shift_type,
                    'start_time': hist_shift['start_time'],
                    'end_time': hist_shift['end_time'],
                    'grace_period_minutes': hist_shift.get('grace_period_minutes', 10)
                }

        # 3) Fallback to current shift.
        return default_shift
    
    def _process_leave_data(self, leave_data: List[Dict], per_day_salary: float, 
                          year: int, month: int) -> Dict:
        """Process leave data for salary calculations"""
        total_leave_days = 0
        leave_pay = 0.0
        
        for leave in leave_data:
            leave_type = leave['leave_type'].lower()

            # Calculate days from start_date and end_date (handle both string and date objects)
            start_date = self._to_date(leave['start_date'])
            end_date = self._to_date(leave['end_date'])

            # Only count days within the requested month
            month_start = datetime(year, month, 1).date()
            month_end = datetime(year, month, calendar.monthrange(year, month)[1]).date()

            # Adjust dates to be within the month
            actual_start = max(start_date, month_start)
            actual_end = min(end_date, month_end)

            if actual_start <= actual_end:
                days = (actual_end - actual_start).days + 1

                # Apply leave rate based on type
                if leave_type in ['sick_leave', 'sl']:
                    rate = self.salary_rules['sick_leave_rate']
                elif leave_type in ['casual_leave', 'cl']:
                    rate = self.salary_rules['casual_leave_rate']
                elif leave_type in ['earned_leave', 'el']:
                    rate = self.salary_rules['earned_leave_rate']
                elif leave_type in ['maternity_leave', 'ml']:
                    rate = self.salary_rules['maternity_leave_rate']
                elif leave_type == 'permission':
                    rate = self.salary_rules['permission_deduction_rate']
                else:
                    rate = self.salary_rules['unpaid_leave_rate']

                total_leave_days += days
                leave_pay += days * per_day_salary * rate
        
        return {
            'total_leave_days': total_leave_days,
            'leave_pay': leave_pay
        }
    
    def _get_staff_shift_info(self, staff_id: int) -> Optional[Dict]:
        """Get shift information for staff member"""
        try:
            db = self._get_db_connection()
            # Try to get shift info from staff table only (shifts table may not exist)
            staff = db.execute('''
                SELECT shift_type
                FROM staff
                WHERE id = ?
            ''', (staff_id,)).fetchone()

            if staff and staff['shift_type']:
                shift_type = staff['shift_type']
                
                # Get actual shift definition from database
                shift_def = db.execute('''
                    SELECT start_time, end_time, grace_period_minutes
                    FROM shift_definitions
                    WHERE shift_type = ? AND is_active = 1
                    ORDER BY id DESC
                    LIMIT 1
                ''', (shift_type,)).fetchone()
                
                if shift_def:
                    return {
                        'shift_type': shift_type,
                        'start_time': shift_def['start_time'],
                        'end_time': shift_def['end_time'],
                        'grace_period_minutes': shift_def['grace_period_minutes']
                    }
                else:
                    # Fallback to default values if shift definition not found
                    return {
                        'shift_type': shift_type,
                        'start_time': '09:00:00',
                        'end_time': '17:00:00',
                        'grace_period_minutes': 10
                    }
        except Exception as e:
            print(f"Error getting staff shift info: {e}")

        # Default shift if not found or error
        return {
            'shift_type': 'general',
            'start_time': '09:00:00',
            'end_time': '17:00:00',
            'grace_period_minutes': 10
        }
    
    def _calculate_early_arrival_minutes(self, actual_time: str, shift_start: str) -> int:
        """Calculate minutes of early arrival"""
        try:
            actual = datetime.strptime(actual_time, '%H:%M:%S').time()
            shift = datetime.strptime(shift_start, '%H:%M:%S').time()
            
            actual_dt = datetime.combine(datetime.today(), actual)
            shift_dt = datetime.combine(datetime.today(), shift)
            
            if actual_dt < shift_dt:
                return int((shift_dt - actual_dt).total_seconds() / 60)
            return 0
        except:
            return 0
    
    def _calculate_early_departure_minutes(self, actual_time: str, shift_end: str, shift_start: str = None) -> int:
        """Calculate minutes of early departure, accounting for night shifts crossing midnight"""
        try:
            actual = datetime.strptime(actual_time, '%H:%M:%S').time()
            shift_end_time = datetime.strptime(shift_end, '%H:%M:%S').time()
            
            today = datetime.today()
            actual_dt = datetime.combine(today, actual)
            shift_dt = datetime.combine(today, shift_end_time)
            
            # Handle overnight shifts (shift_end < shift_start indicates crossing midnight)
            if shift_start:
                try:
                    shift_start_time = datetime.strptime(shift_start, '%H:%M:%S').time()
                    
                    # If shift crosses midnight (end_time < start_time)
                    if shift_end_time < shift_start_time:
                        # Shift ends on next day
                        shift_dt = datetime.combine(today + timedelta(days=1), shift_end_time)

                        # Only treat as next-day checkout for true post-midnight times
                        # (00:00 .. shift_end). Daytime times between shift_end and shift_start
                        # remain on the same day and should still be treated as early departure.
                        if actual <= shift_end_time:
                            actual_dt = datetime.combine(today + timedelta(days=1), actual)
                except (ValueError, TypeError):
                    pass
            
            if actual_dt < shift_dt:
                return int((shift_dt - actual_dt).total_seconds() / 60)
            return 0
        except:
            return 0

    def _calculate_overtime_hours(self, overtime_in: str, overtime_out: str) -> float:
        """Calculate overtime hours from overtime_in and overtime_out times"""
        try:
            if not overtime_in or not overtime_out:
                return 0.0

            overtime_in_time = datetime.strptime(overtime_in, '%H:%M:%S').time()
            overtime_out_time = datetime.strptime(overtime_out, '%H:%M:%S').time()

            overtime_in_dt = datetime.combine(datetime.today(), overtime_in_time)
            overtime_out_dt = datetime.combine(datetime.today(), overtime_out_time)

            # Handle overnight overtime
            if overtime_out_dt < overtime_in_dt:
                overtime_out_dt += timedelta(days=1)

            overtime_duration = overtime_out_dt - overtime_in_dt
            return overtime_duration.total_seconds() / 3600  # Convert to hours
        except:
            return 0.0

    def generate_salary_report(self, staff_id: int, year: int, month: int) -> Dict:
        """Generate a comprehensive salary report"""
        salary_data = self.calculate_monthly_salary(staff_id, year, month)
        
        if not salary_data['success']:
            return salary_data
        
        # Add additional report information
        report_data = salary_data.copy()
        report_data['report_generated_at'] = datetime.now().isoformat()
        report_data['report_type'] = 'Monthly Salary Report'
        
        return report_data
    
    def update_salary_rules(self, new_rules: Dict) -> Dict:
        """Update salary calculation rules and persist to database"""
        try:
            # Update in-memory rules
            self.salary_rules.update(new_rules)
            
            # Save to database
            if self._save_salary_rules_to_db(new_rules):
                return {'success': True, 'message': 'Salary rules updated and saved successfully'}
            else:
                error_message = self._last_salary_rules_error or 'Failed to save salary rules to database'
                return {'success': False, 'error': error_message}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_salary_rules(self) -> Dict:
        """Get current salary rules"""
        return {
            'success': True,
            'salary_rules': self.salary_rules
        }
