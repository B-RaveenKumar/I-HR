# reporting_dashboard.py
"""
Comprehensive Reporting Dashboard

This module provides advanced reporting capabilities including:
- Daily, weekly, monthly, yearly reports
- Department-wise analysis
- Custom date range reports
- Attendance trends and analytics
- Performance metrics
- Export capabilities
"""

from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
from database import get_db
import calendar
import json


class ReportingDashboard:
    """Comprehensive reporting dashboard for attendance management"""
    
    def __init__(self):
        self.report_types = [
            'daily', 'weekly', 'monthly', 'yearly', 
            'department', 'custom', 'summary', 'trends'
        ]
    
    def generate_daily_report(self, school_id: int, report_date: str) -> Dict:
        """Generate daily attendance report"""
        db = get_db()
        
        # Basic attendance statistics
        daily_stats = db.execute('''
            SELECT 
                COUNT(*) as total_staff,
                COUNT(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1 END) as present_count,
                COUNT(CASE WHEN a.status = 'absent' THEN 1 END) as absent_count,
                COUNT(CASE WHEN a.status = 'late' THEN 1 END) as late_count,
                COUNT(CASE WHEN a.status = 'leave' THEN 1 END) as leave_count,
                COUNT(CASE WHEN a.status = 'on_duty' THEN 1 END) as on_duty_count,
                AVG(CASE WHEN a.work_hours IS NOT NULL THEN a.work_hours END) as avg_work_hours,
                SUM(CASE WHEN a.overtime_hours IS NOT NULL THEN a.overtime_hours ELSE 0 END) as total_overtime
            FROM staff s
            LEFT JOIN attendance a ON s.id = a.staff_id AND a.date = ?
            WHERE s.school_id = ?
        ''', (report_date, school_id)).fetchone()
        
        # Department-wise breakdown
        dept_breakdown = db.execute('''
            SELECT 
                COALESCE(s.department, 'Unassigned') as department,
                COUNT(s.id) as total_staff,
                COUNT(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1 END) as present_count,
                COUNT(CASE WHEN a.status = 'late' THEN 1 END) as late_count,
                AVG(CASE WHEN a.work_hours IS NOT NULL THEN a.work_hours END) as avg_work_hours
            FROM staff s
            LEFT JOIN attendance a ON s.id = a.staff_id AND a.date = ?
            WHERE s.school_id = ?
            GROUP BY s.department
            ORDER BY present_count DESC
        ''', (report_date, school_id)).fetchall()
        
        # Late arrivals details
        late_arrivals = db.execute('''
            SELECT s.staff_id, s.full_name, s.department, a.time_in, a.late_duration_minutes
            FROM staff s
            JOIN attendance a ON s.id = a.staff_id
            WHERE s.school_id = ? AND a.date = ? AND a.status = 'late'
            ORDER BY a.late_duration_minutes DESC
        ''', (school_id, report_date)).fetchall()
        
        # Overtime details
        overtime_details = db.execute('''
            SELECT s.staff_id, s.full_name, s.department, a.overtime_hours, a.overtime_in, a.overtime_out
            FROM staff s
            JOIN attendance a ON s.id = a.staff_id
            WHERE s.school_id = ? AND a.date = ? AND a.overtime_hours > 0
            ORDER BY a.overtime_hours DESC
        ''', (school_id, report_date)).fetchall()
        
        return {
            'report_type': 'daily',
            'report_date': report_date,
            'statistics': dict(daily_stats),
            'department_breakdown': [dict(row) for row in dept_breakdown],
            'late_arrivals': [dict(row) for row in late_arrivals],
            'overtime_details': [dict(row) for row in overtime_details],
            'attendance_rate': (daily_stats['present_count'] / daily_stats['total_staff'] * 100) if daily_stats['total_staff'] > 0 else 0
        }
    
    def generate_weekly_report(self, school_id: int, start_date: str, end_date: str) -> Dict:
        """Generate weekly attendance report"""
        db = get_db()
        
        # Weekly statistics
        weekly_stats = db.execute('''
            SELECT 
                COUNT(DISTINCT s.id) as total_staff,
                COUNT(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1 END) as total_present,
                COUNT(CASE WHEN a.status = 'absent' THEN 1 END) as total_absent,
                COUNT(CASE WHEN a.status = 'late' THEN 1 END) as total_late,
                COUNT(CASE WHEN a.status = 'leave' THEN 1 END) as total_leave,
                AVG(CASE WHEN a.work_hours IS NOT NULL THEN a.work_hours END) as avg_work_hours,
                SUM(CASE WHEN a.overtime_hours IS NOT NULL THEN a.overtime_hours ELSE 0 END) as total_overtime,
                COUNT(DISTINCT a.date) as working_days
            FROM staff s
            LEFT JOIN attendance a ON s.id = a.staff_id AND a.date BETWEEN ? AND ?
            WHERE s.school_id = ?
        ''', (start_date, end_date, school_id)).fetchone()
        
        # Daily breakdown
        daily_breakdown = db.execute('''
            SELECT 
                a.date,
                COUNT(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1 END) as present_count,
                COUNT(CASE WHEN a.status = 'absent' THEN 1 END) as absent_count,
                COUNT(CASE WHEN a.status = 'late' THEN 1 END) as late_count,
                AVG(CASE WHEN a.work_hours IS NOT NULL THEN a.work_hours END) as avg_work_hours,
                SUM(CASE WHEN a.overtime_hours IS NOT NULL THEN a.overtime_hours ELSE 0 END) as daily_overtime
            FROM attendance a
            JOIN staff s ON a.staff_id = s.id
            WHERE s.school_id = ? AND a.date BETWEEN ? AND ?
            GROUP BY a.date
            ORDER BY a.date
        ''', (school_id, start_date, end_date)).fetchall()
        
        # Top performers (by attendance rate)
        top_performers = db.execute('''
            SELECT 
                s.staff_id, s.full_name, s.department,
                COUNT(a.id) as total_days,
                COUNT(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1 END) as present_days,
                ROUND(COUNT(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1 END) * 100.0 / COUNT(a.id), 2) as attendance_rate,
                SUM(CASE WHEN a.overtime_hours IS NOT NULL THEN a.overtime_hours ELSE 0 END) as total_overtime
            FROM staff s
            LEFT JOIN attendance a ON s.id = a.staff_id AND a.date BETWEEN ? AND ?
            WHERE s.school_id = ?
            GROUP BY s.id
            HAVING total_days > 0
            ORDER BY attendance_rate DESC, total_overtime DESC
            LIMIT 10
        ''', (start_date, end_date, school_id)).fetchall()
        
        return {
            'report_type': 'weekly',
            'start_date': start_date,
            'end_date': end_date,
            'statistics': dict(weekly_stats),
            'daily_breakdown': [dict(row) for row in daily_breakdown],
            'top_performers': [dict(row) for row in top_performers],
            'avg_attendance_rate': (weekly_stats['total_present'] / (weekly_stats['total_staff'] * weekly_stats['working_days']) * 100) if weekly_stats['total_staff'] > 0 and weekly_stats['working_days'] > 0 else 0
        }
    
    def generate_monthly_report(self, school_id: int, year: int, month: int) -> Dict:
        """Generate monthly attendance report"""
        db = get_db()
        
        # Calculate month boundaries
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        working_days = self._get_working_days_in_month(year, month)
        
        # Monthly statistics
        monthly_stats = db.execute('''
            SELECT 
                COUNT(DISTINCT s.id) as total_staff,
                COUNT(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1 END) as total_present,
                COUNT(CASE WHEN a.status = 'absent' THEN 1 END) as total_absent,
                COUNT(CASE WHEN a.status = 'late' THEN 1 END) as total_late,
                COUNT(CASE WHEN a.status = 'leave' THEN 1 END) as total_leave,
                AVG(CASE WHEN a.work_hours IS NOT NULL THEN a.work_hours END) as avg_work_hours,
                SUM(CASE WHEN a.overtime_hours IS NOT NULL THEN a.overtime_hours ELSE 0 END) as total_overtime
            FROM staff s
            LEFT JOIN attendance a ON s.id = a.staff_id AND a.date BETWEEN ? AND ?
            WHERE s.school_id = ?
        ''', (start_date, end_date, school_id)).fetchone()
        
        # Weekly breakdown
        weekly_breakdown = []
        current_date = start_date
        week_num = 1
        
        while current_date <= end_date:
            week_end = min(current_date + timedelta(days=6), end_date)
            
            week_stats = db.execute('''
                SELECT 
                    COUNT(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1 END) as present_count,
                    COUNT(CASE WHEN a.status = 'absent' THEN 1 END) as absent_count,
                    COUNT(CASE WHEN a.status = 'late' THEN 1 END) as late_count,
                    AVG(CASE WHEN a.work_hours IS NOT NULL THEN a.work_hours END) as avg_work_hours,
                    SUM(CASE WHEN a.overtime_hours IS NOT NULL THEN a.overtime_hours ELSE 0 END) as weekly_overtime
                FROM attendance a
                JOIN staff s ON a.staff_id = s.id
                WHERE s.school_id = ? AND a.date BETWEEN ? AND ?
            ''', (school_id, current_date, week_end)).fetchone()
            
            weekly_breakdown.append({
                'week': week_num,
                'start_date': current_date.strftime('%Y-%m-%d'),
                'end_date': week_end.strftime('%Y-%m-%d'),
                **dict(week_stats)
            })
            
            current_date = week_end + timedelta(days=1)
            week_num += 1
        
        # Department performance
        dept_performance = db.execute('''
            SELECT 
                COALESCE(s.department, 'Unassigned') as department,
                COUNT(DISTINCT s.id) as total_staff,
                COUNT(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1 END) as present_count,
                COUNT(CASE WHEN a.status = 'late' THEN 1 END) as late_count,
                ROUND(COUNT(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1 END) * 100.0 / 
                      (COUNT(DISTINCT s.id) * ?), 2) as attendance_rate,
                SUM(CASE WHEN a.overtime_hours IS NOT NULL THEN a.overtime_hours ELSE 0 END) as total_overtime
            FROM staff s
            LEFT JOIN attendance a ON s.id = a.staff_id AND a.date BETWEEN ? AND ?
            WHERE s.school_id = ?
            GROUP BY s.department
            ORDER BY attendance_rate DESC
        ''', (working_days, start_date, end_date, school_id)).fetchall()
        
        return {
            'report_type': 'monthly',
            'year': year,
            'month': month,
            'month_name': calendar.month_name[month],
            'working_days': working_days,
            'statistics': dict(monthly_stats),
            'weekly_breakdown': weekly_breakdown,
            'department_performance': [dict(row) for row in dept_performance],
            'avg_attendance_rate': (monthly_stats['total_present'] / (monthly_stats['total_staff'] * working_days) * 100) if monthly_stats['total_staff'] > 0 else 0
        }
    
    def generate_yearly_report(self, school_id: int, year: int) -> Dict:
        """Generate yearly attendance report"""
        db = get_db()
        
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        
        # Yearly statistics
        yearly_stats = db.execute('''
            SELECT 
                COUNT(DISTINCT s.id) as total_staff,
                COUNT(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1 END) as total_present,
                COUNT(CASE WHEN a.status = 'absent' THEN 1 END) as total_absent,
                COUNT(CASE WHEN a.status = 'late' THEN 1 END) as total_late,
                COUNT(CASE WHEN a.status = 'leave' THEN 1 END) as total_leave,
                AVG(CASE WHEN a.work_hours IS NOT NULL THEN a.work_hours END) as avg_work_hours,
                SUM(CASE WHEN a.overtime_hours IS NOT NULL THEN a.overtime_hours ELSE 0 END) as total_overtime,
                COUNT(DISTINCT a.date) as working_days
            FROM staff s
            LEFT JOIN attendance a ON s.id = a.staff_id AND a.date BETWEEN ? AND ?
            WHERE s.school_id = ?
        ''', (start_date, end_date, school_id)).fetchone()
        
        # Monthly breakdown
        monthly_breakdown = []
        for month in range(1, 13):
            month_start = date(year, month, 1)
            if month == 12:
                month_end = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                month_end = date(year, month + 1, 1) - timedelta(days=1)
            
            month_stats = db.execute('''
                SELECT 
                    COUNT(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1 END) as present_count,
                    COUNT(CASE WHEN a.status = 'absent' THEN 1 END) as absent_count,
                    COUNT(CASE WHEN a.status = 'late' THEN 1 END) as late_count,
                    AVG(CASE WHEN a.work_hours IS NOT NULL THEN a.work_hours END) as avg_work_hours,
                    SUM(CASE WHEN a.overtime_hours IS NOT NULL THEN a.overtime_hours ELSE 0 END) as monthly_overtime
                FROM attendance a
                JOIN staff s ON a.staff_id = s.id
                WHERE s.school_id = ? AND a.date BETWEEN ? AND ?
            ''', (school_id, month_start, month_end)).fetchone()
            
            monthly_breakdown.append({
                'month': month,
                'month_name': calendar.month_name[month],
                **dict(month_stats)
            })
        
        return {
            'report_type': 'yearly',
            'year': year,
            'statistics': dict(yearly_stats),
            'monthly_breakdown': monthly_breakdown,
            'avg_attendance_rate': (yearly_stats['total_present'] / (yearly_stats['total_staff'] * yearly_stats['working_days']) * 100) if yearly_stats['total_staff'] > 0 and yearly_stats['working_days'] > 0 else 0
        }
    
    def _get_working_days_in_month(self, year: int, month: int) -> int:
        """Calculate working days in a month (excluding only Sundays)"""
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        working_days = 0
        current_date = start_date
        
        while current_date <= end_date:
            # Monday = 0, Sunday = 6
            if current_date.weekday() < 6:  # Monday to Saturday
                working_days += 1
            current_date += timedelta(days=1)
        
        return working_days

    def generate_department_report(self, school_id: int, department: str,
                                 start_date: str, end_date: str) -> Dict:
        """Generate department-specific report"""
        db = get_db()

        # Department statistics
        dept_stats = db.execute('''
            SELECT
                COUNT(DISTINCT s.id) as total_staff,
                COUNT(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1 END) as total_present,
                COUNT(CASE WHEN a.status = 'absent' THEN 1 END) as total_absent,
                COUNT(CASE WHEN a.status = 'late' THEN 1 END) as total_late,
                COUNT(CASE WHEN a.status = 'leave' THEN 1 END) as total_leave,
                AVG(CASE WHEN a.work_hours IS NOT NULL THEN a.work_hours END) as avg_work_hours,
                SUM(CASE WHEN a.overtime_hours IS NOT NULL THEN a.overtime_hours ELSE 0 END) as total_overtime,
                COUNT(DISTINCT a.date) as working_days
            FROM staff s
            LEFT JOIN attendance a ON s.id = a.staff_id AND a.date BETWEEN ? AND ?
            WHERE s.school_id = ? AND s.department = ?
        ''', (start_date, end_date, school_id, department)).fetchone()

        # Staff performance in department
        staff_performance = db.execute('''
            SELECT
                s.staff_id, s.full_name, s.position,
                COUNT(a.id) as total_days,
                COUNT(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1 END) as present_days,
                COUNT(CASE WHEN a.status = 'late' THEN 1 END) as late_days,
                ROUND(COUNT(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1 END) * 100.0 / COUNT(a.id), 2) as attendance_rate,
                AVG(CASE WHEN a.work_hours IS NOT NULL THEN a.work_hours END) as avg_work_hours,
                SUM(CASE WHEN a.overtime_hours IS NOT NULL THEN a.overtime_hours ELSE 0 END) as total_overtime
            FROM staff s
            LEFT JOIN attendance a ON s.id = a.staff_id AND a.date BETWEEN ? AND ?
            WHERE s.school_id = ? AND s.department = ?
            GROUP BY s.id
            ORDER BY attendance_rate DESC, total_overtime DESC
        ''', (start_date, end_date, school_id, department)).fetchall()

        return {
            'report_type': 'department',
            'department': department,
            'start_date': start_date,
            'end_date': end_date,
            'statistics': dict(dept_stats),
            'staff_performance': [dict(row) for row in staff_performance],
            'avg_attendance_rate': (dept_stats['total_present'] / (dept_stats['total_staff'] * dept_stats['working_days']) * 100) if dept_stats['total_staff'] > 0 and dept_stats['working_days'] > 0 else 0
        }

    def generate_custom_report(self, school_id: int, filters: Dict) -> Dict:
        """Generate custom report based on filters"""
        db = get_db()

        # Build dynamic query based on filters
        where_conditions = ['s.school_id = ?']
        params = [school_id]

        if filters.get('start_date') and filters.get('end_date'):
            where_conditions.append('a.date BETWEEN ? AND ?')
            params.extend([filters['start_date'], filters['end_date']])

        if filters.get('department'):
            where_conditions.append('s.department = ?')
            params.append(filters['department'])

        if filters.get('position'):
            where_conditions.append('s.position = ?')
            params.append(filters['position'])

        if filters.get('status'):
            where_conditions.append('a.status = ?')
            params.append(filters['status'])

        # Custom statistics
        custom_stats = db.execute(f'''
            SELECT
                COUNT(DISTINCT s.id) as total_staff,
                COUNT(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1 END) as total_present,
                COUNT(CASE WHEN a.status = 'absent' THEN 1 END) as total_absent,
                COUNT(CASE WHEN a.status = 'late' THEN 1 END) as total_late,
                COUNT(CASE WHEN a.status = 'leave' THEN 1 END) as total_leave,
                AVG(CASE WHEN a.work_hours IS NOT NULL THEN a.work_hours END) as avg_work_hours,
                SUM(CASE WHEN a.overtime_hours IS NOT NULL THEN a.overtime_hours ELSE 0 END) as total_overtime,
                COUNT(DISTINCT a.date) as working_days
            FROM staff s
            LEFT JOIN attendance a ON s.id = a.staff_id
            WHERE {' AND '.join(where_conditions)}
        ''', params).fetchone()

        # Detailed records
        detailed_records = db.execute(f'''
            SELECT
                s.staff_id, s.full_name, s.department, s.position,
                a.date, a.time_in, a.time_out, a.status, a.work_hours, a.overtime_hours
            FROM staff s
            LEFT JOIN attendance a ON s.id = a.staff_id
            WHERE {' AND '.join(where_conditions)}
            ORDER BY a.date DESC, s.full_name
            LIMIT 1000
        ''', params).fetchall()

        return {
            'report_type': 'custom',
            'filters': filters,
            'statistics': dict(custom_stats),
            'detailed_records': [dict(row) for row in detailed_records],
            'record_count': len(detailed_records)
        }

    def generate_trends_report(self, school_id: int, start_date: str, end_date: str) -> Dict:
        """Generate attendance trends and analytics report"""
        db = get_db()

        # Daily trends
        daily_trends = db.execute('''
            SELECT
                a.date,
                COUNT(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1 END) as present_count,
                COUNT(CASE WHEN a.status = 'absent' THEN 1 END) as absent_count,
                COUNT(CASE WHEN a.status = 'late' THEN 1 END) as late_count,
                AVG(CASE WHEN a.work_hours IS NOT NULL THEN a.work_hours END) as avg_work_hours,
                SUM(CASE WHEN a.overtime_hours IS NOT NULL THEN a.overtime_hours ELSE 0 END) as daily_overtime
            FROM attendance a
            JOIN staff s ON a.staff_id = s.id
            WHERE s.school_id = ? AND a.date BETWEEN ? AND ?
            GROUP BY a.date
            ORDER BY a.date
        ''', (school_id, start_date, end_date)).fetchall()

        # Weekly patterns (day of week analysis)
        weekly_patterns = db.execute('''
            SELECT
                CASE strftime('%w', a.date)
                    WHEN '0' THEN 'Sunday'
                    WHEN '1' THEN 'Monday'
                    WHEN '2' THEN 'Tuesday'
                    WHEN '3' THEN 'Wednesday'
                    WHEN '4' THEN 'Thursday'
                    WHEN '5' THEN 'Friday'
                    WHEN '6' THEN 'Saturday'
                END as day_of_week,
                AVG(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1.0 ELSE 0.0 END) * 100 as avg_attendance_rate,
                AVG(CASE WHEN a.status = 'late' THEN 1.0 ELSE 0.0 END) * 100 as avg_late_rate,
                AVG(CASE WHEN a.work_hours IS NOT NULL THEN a.work_hours END) as avg_work_hours
            FROM attendance a
            JOIN staff s ON a.staff_id = s.id
            WHERE s.school_id = ? AND a.date BETWEEN ? AND ?
            GROUP BY strftime('%w', a.date)
            ORDER BY strftime('%w', a.date)
        ''', (school_id, start_date, end_date)).fetchall()

        # Monthly trends
        monthly_trends = db.execute('''
            SELECT
                strftime('%Y-%m', a.date) as month,
                AVG(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1.0 ELSE 0.0 END) * 100 as avg_attendance_rate,
                AVG(CASE WHEN a.status = 'late' THEN 1.0 ELSE 0.0 END) * 100 as avg_late_rate,
                AVG(CASE WHEN a.work_hours IS NOT NULL THEN a.work_hours END) as avg_work_hours,
                SUM(CASE WHEN a.overtime_hours IS NOT NULL THEN a.overtime_hours ELSE 0 END) as monthly_overtime
            FROM attendance a
            JOIN staff s ON a.staff_id = s.id
            WHERE s.school_id = ? AND a.date BETWEEN ? AND ?
            GROUP BY strftime('%Y-%m', a.date)
            ORDER BY month
        ''', (school_id, start_date, end_date)).fetchall()

        return {
            'report_type': 'trends',
            'start_date': start_date,
            'end_date': end_date,
            'daily_trends': [dict(row) for row in daily_trends],
            'weekly_patterns': [dict(row) for row in weekly_patterns],
            'monthly_trends': [dict(row) for row in monthly_trends]
        }

    def get_summary_dashboard(self, school_id: int) -> Dict:
        """Get summary dashboard data"""
        db = get_db()
        today = datetime.now().date()

        # Today's summary
        today_summary = db.execute('''
            SELECT
                COUNT(DISTINCT s.id) as total_staff,
                COUNT(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1 END) as present_today,
                COUNT(CASE WHEN a.status = 'absent' THEN 1 END) as absent_today,
                COUNT(CASE WHEN a.status = 'late' THEN 1 END) as late_today,
                COUNT(CASE WHEN a.status = 'leave' THEN 1 END) as leave_today
            FROM staff s
            LEFT JOIN attendance a ON s.id = a.staff_id AND a.date = ?
            WHERE s.school_id = ?
        ''', (today, school_id)).fetchone()

        # This month's summary
        month_start = today.replace(day=1)
        month_summary = db.execute('''
            SELECT
                COUNT(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1 END) as present_month,
                COUNT(CASE WHEN a.status = 'absent' THEN 1 END) as absent_month,
                COUNT(CASE WHEN a.status = 'late' THEN 1 END) as late_month,
                SUM(CASE WHEN a.overtime_hours IS NOT NULL THEN a.overtime_hours ELSE 0 END) as overtime_month
            FROM attendance a
            JOIN staff s ON a.staff_id = s.id
            WHERE s.school_id = ? AND a.date >= ?
        ''', (school_id, month_start)).fetchone()

        # Recent trends (last 7 days)
        week_ago = today - timedelta(days=7)
        recent_trends = db.execute('''
            SELECT
                a.date,
                COUNT(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1 END) as present_count,
                COUNT(CASE WHEN a.status = 'late' THEN 1 END) as late_count
            FROM attendance a
            JOIN staff s ON a.staff_id = s.id
            WHERE s.school_id = ? AND a.date >= ?
            GROUP BY a.date
            ORDER BY a.date
        ''', (school_id, week_ago)).fetchall()

        return {
            'today_summary': dict(today_summary),
            'month_summary': dict(month_summary),
            'recent_trends': [dict(row) for row in recent_trends],
            'attendance_rate_today': (today_summary['present_today'] / today_summary['total_staff'] * 100) if today_summary['total_staff'] > 0 else 0
        }
