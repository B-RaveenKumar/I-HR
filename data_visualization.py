# data_visualization.py
"""
Data Visualization and Analytics Module

This module provides advanced data visualization and analytics features including:
- Interactive charts and graphs
- Attendance pattern analysis
- Trend identification
- Performance metrics visualization
- Predictive analytics
- Dashboard widgets
"""

import json
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
from database import get_db
import calendar


class DataVisualization:
    """Advanced data visualization and analytics for attendance system"""
    
    def __init__(self):
        self.chart_colors = [
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', 
            '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF',
            '#4BC0C0', '#FF9F40', '#36A2EB', '#FFCE56'
        ]
    
    def generate_attendance_pie_chart(self, school_id: int, start_date: str, end_date: str) -> Dict:
        """Generate pie chart data for attendance status distribution"""
        db = get_db()
        
        status_data = db.execute('''
            SELECT 
                CASE 
                    WHEN status IN ('present', 'late', 'on_duty') THEN 'Present'
                    WHEN status = 'absent' THEN 'Absent'
                    WHEN status = 'leave' THEN 'On Leave'
                    ELSE 'Other'
                END as status_group,
                COUNT(*) as count
            FROM attendance a
            JOIN staff s ON a.staff_id = s.id
            WHERE s.school_id = ? AND a.date BETWEEN ? AND ?
            GROUP BY status_group
            ORDER BY count DESC
        ''', (school_id, start_date, end_date)).fetchall()
        
        return {
            'type': 'pie',
            'title': 'Attendance Status Distribution',
            'labels': [row['status_group'] for row in status_data],
            'data': [row['count'] for row in status_data],
            'backgroundColor': self.chart_colors[:len(status_data)],
            'total_records': sum(row['count'] for row in status_data)
        }
    
    def generate_daily_trends_chart(self, school_id: int, start_date: str, end_date: str) -> Dict:
        """Generate line chart for daily attendance trends"""
        db = get_db()
        
        daily_data = db.execute('''
            SELECT 
                a.date,
                COUNT(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1 END) as present_count,
                COUNT(CASE WHEN a.status = 'absent' THEN 1 END) as absent_count,
                COUNT(CASE WHEN a.status = 'late' THEN 1 END) as late_count,
                COUNT(*) as total_count
            FROM attendance a
            JOIN staff s ON a.staff_id = s.id
            WHERE s.school_id = ? AND a.date BETWEEN ? AND ?
            GROUP BY a.date
            ORDER BY a.date
        ''', (school_id, start_date, end_date)).fetchall()
        
        return {
            'type': 'line',
            'title': 'Daily Attendance Trends',
            'labels': [row['date'] for row in daily_data],
            'datasets': [
                {
                    'label': 'Present',
                    'data': [row['present_count'] for row in daily_data],
                    'borderColor': '#28a745',
                    'backgroundColor': 'rgba(40, 167, 69, 0.1)',
                    'fill': True
                },
                {
                    'label': 'Absent',
                    'data': [row['absent_count'] for row in daily_data],
                    'borderColor': '#dc3545',
                    'backgroundColor': 'rgba(220, 53, 69, 0.1)',
                    'fill': True
                },
                {
                    'label': 'Late',
                    'data': [row['late_count'] for row in daily_data],
                    'borderColor': '#ffc107',
                    'backgroundColor': 'rgba(255, 193, 7, 0.1)',
                    'fill': True
                }
            ]
        }
    
    def generate_department_comparison_chart(self, school_id: int, start_date: str, end_date: str) -> Dict:
        """Generate bar chart for department-wise attendance comparison"""
        db = get_db()
        
        dept_data = db.execute('''
            SELECT 
                COALESCE(s.department, 'Unassigned') as department,
                COUNT(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1 END) as present_count,
                COUNT(*) as total_count,
                ROUND(COUNT(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1 END) * 100.0 / COUNT(*), 2) as attendance_rate
            FROM staff s
            LEFT JOIN attendance a ON s.id = a.staff_id AND a.date BETWEEN ? AND ?
            WHERE s.school_id = ?
            GROUP BY s.department
            HAVING total_count > 0
            ORDER BY attendance_rate DESC
        ''', (start_date, end_date, school_id)).fetchall()
        
        return {
            'type': 'bar',
            'title': 'Department-wise Attendance Rate',
            'labels': [row['department'] for row in dept_data],
            'datasets': [
                {
                    'label': 'Attendance Rate (%)',
                    'data': [row['attendance_rate'] for row in dept_data],
                    'backgroundColor': self.chart_colors[:len(dept_data)],
                    'borderColor': self.chart_colors[:len(dept_data)],
                    'borderWidth': 1
                }
            ],
            'options': {
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'max': 100,
                        'ticks': {
                            'callback': 'function(value) { return value + "%"; }'
                        }
                    }
                }
            }
        }
    
    def generate_weekly_pattern_chart(self, school_id: int, start_date: str, end_date: str) -> Dict:
        """Generate chart showing weekly attendance patterns"""
        db = get_db()
        
        weekly_data = db.execute('''
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
                strftime('%w', a.date) as day_num,
                AVG(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1.0 ELSE 0.0 END) * 100 as avg_attendance_rate,
                AVG(CASE WHEN a.status = 'late' THEN 1.0 ELSE 0.0 END) * 100 as avg_late_rate,
                COUNT(*) as total_records
            FROM attendance a
            JOIN staff s ON a.staff_id = s.id
            WHERE s.school_id = ? AND a.date BETWEEN ? AND ?
            GROUP BY strftime('%w', a.date)
            ORDER BY day_num
        ''', (school_id, start_date, end_date)).fetchall()
        
        return {
            'type': 'radar',
            'title': 'Weekly Attendance Pattern',
            'labels': [row['day_of_week'] for row in weekly_data],
            'datasets': [
                {
                    'label': 'Attendance Rate (%)',
                    'data': [round(row['avg_attendance_rate'], 1) for row in weekly_data],
                    'borderColor': '#007bff',
                    'backgroundColor': 'rgba(0, 123, 255, 0.2)',
                    'pointBackgroundColor': '#007bff',
                    'pointBorderColor': '#fff',
                    'pointHoverBackgroundColor': '#fff',
                    'pointHoverBorderColor': '#007bff'
                },
                {
                    'label': 'Late Rate (%)',
                    'data': [round(row['avg_late_rate'], 1) for row in weekly_data],
                    'borderColor': '#ffc107',
                    'backgroundColor': 'rgba(255, 193, 7, 0.2)',
                    'pointBackgroundColor': '#ffc107',
                    'pointBorderColor': '#fff',
                    'pointHoverBackgroundColor': '#fff',
                    'pointHoverBorderColor': '#ffc107'
                }
            ]
        }
    
    def generate_monthly_heatmap_data(self, school_id: int, year: int, month: int) -> Dict:
        """Generate heatmap data for monthly attendance"""
        db = get_db()
        
        # Get all days in the month
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        daily_data = db.execute('''
            SELECT 
                a.date,
                COUNT(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1 END) as present_count,
                COUNT(*) as total_count,
                ROUND(COUNT(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1 END) * 100.0 / COUNT(*), 2) as attendance_rate
            FROM attendance a
            JOIN staff s ON a.staff_id = s.id
            WHERE s.school_id = ? AND a.date BETWEEN ? AND ?
            GROUP BY a.date
            ORDER BY a.date
        ''', (school_id, start_date, end_date)).fetchall()
        
        # Create calendar grid data
        calendar_data = []
        current_date = start_date
        
        # Create a lookup for attendance data
        attendance_lookup = {row['date']: row for row in daily_data}
        
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            attendance_info = attendance_lookup.get(date_str, {
                'present_count': 0,
                'total_count': 0,
                'attendance_rate': 0
            })
            
            calendar_data.append({
                'date': date_str,
                'day': current_date.day,
                'weekday': current_date.weekday(),
                'attendance_rate': attendance_info['attendance_rate'],
                'present_count': attendance_info['present_count'],
                'total_count': attendance_info['total_count'],
                'is_weekend': current_date.weekday() >= 5
            })
            
            current_date += timedelta(days=1)
        
        return {
            'type': 'heatmap',
            'title': f'Monthly Attendance Heatmap - {calendar.month_name[month]} {year}',
            'data': calendar_data,
            'month': month,
            'year': year,
            'month_name': calendar.month_name[month]
        }
    
    def generate_overtime_analysis_chart(self, school_id: int, start_date: str, end_date: str) -> Dict:
        """Generate chart for overtime analysis"""
        db = get_db()
        
        overtime_data = db.execute('''
            SELECT 
                s.department,
                SUM(CASE WHEN a.overtime_hours IS NOT NULL THEN a.overtime_hours ELSE 0 END) as total_overtime,
                COUNT(CASE WHEN a.overtime_hours > 0 THEN 1 END) as overtime_days,
                AVG(CASE WHEN a.overtime_hours > 0 THEN a.overtime_hours END) as avg_overtime_per_day
            FROM staff s
            LEFT JOIN attendance a ON s.id = a.staff_id AND a.date BETWEEN ? AND ?
            WHERE s.school_id = ?
            GROUP BY s.department
            HAVING total_overtime > 0
            ORDER BY total_overtime DESC
        ''', (start_date, end_date, school_id)).fetchall()
        
        return {
            'type': 'bar',
            'title': 'Department-wise Overtime Analysis',
            'labels': [row['department'] or 'Unassigned' for row in overtime_data],
            'datasets': [
                {
                    'label': 'Total Overtime Hours',
                    'data': [round(row['total_overtime'], 1) for row in overtime_data],
                    'backgroundColor': '#17a2b8',
                    'borderColor': '#17a2b8',
                    'borderWidth': 1,
                    'yAxisID': 'y'
                },
                {
                    'label': 'Overtime Days',
                    'data': [row['overtime_days'] for row in overtime_data],
                    'backgroundColor': '#fd7e14',
                    'borderColor': '#fd7e14',
                    'borderWidth': 1,
                    'yAxisID': 'y1'
                }
            ],
            'options': {
                'scales': {
                    'y': {
                        'type': 'linear',
                        'display': True,
                        'position': 'left',
                        'title': {
                            'display': True,
                            'text': 'Total Hours'
                        }
                    },
                    'y1': {
                        'type': 'linear',
                        'display': True,
                        'position': 'right',
                        'title': {
                            'display': True,
                            'text': 'Number of Days'
                        },
                        'grid': {
                            'drawOnChartArea': False
                        }
                    }
                }
            }
        }
    
    def generate_performance_metrics(self, school_id: int, start_date: str, end_date: str) -> Dict:
        """Generate performance metrics and KPIs"""
        db = get_db()
        
        # Overall metrics
        overall_metrics = db.execute('''
            SELECT 
                COUNT(DISTINCT s.id) as total_staff,
                COUNT(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1 END) as total_present,
                COUNT(CASE WHEN a.status = 'absent' THEN 1 END) as total_absent,
                COUNT(CASE WHEN a.status = 'late' THEN 1 END) as total_late,
                AVG(CASE WHEN a.work_hours IS NOT NULL THEN a.work_hours END) as avg_work_hours,
                SUM(CASE WHEN a.overtime_hours IS NOT NULL THEN a.overtime_hours ELSE 0 END) as total_overtime,
                COUNT(DISTINCT a.date) as working_days
            FROM staff s
            LEFT JOIN attendance a ON s.id = a.staff_id AND a.date BETWEEN ? AND ?
            WHERE s.school_id = ?
        ''', (start_date, end_date, school_id)).fetchone()
        
        # Calculate KPIs
        total_possible_attendance = overall_metrics['total_staff'] * overall_metrics['working_days']
        attendance_rate = (overall_metrics['total_present'] / total_possible_attendance * 100) if total_possible_attendance > 0 else 0
        punctuality_rate = ((overall_metrics['total_present'] - overall_metrics['total_late']) / overall_metrics['total_present'] * 100) if overall_metrics['total_present'] > 0 else 0
        
        # Top and bottom performers
        top_performers = db.execute('''
            SELECT 
                s.staff_id, s.full_name, s.department,
                COUNT(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1 END) as present_days,
                COUNT(a.id) as total_days,
                ROUND(COUNT(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1 END) * 100.0 / COUNT(a.id), 2) as attendance_rate
            FROM staff s
            LEFT JOIN attendance a ON s.id = a.staff_id AND a.date BETWEEN ? AND ?
            WHERE s.school_id = ?
            GROUP BY s.id
            HAVING total_days > 0
            ORDER BY attendance_rate DESC
            LIMIT 5
        ''', (start_date, end_date, school_id)).fetchall()
        
        return {
            'overall_metrics': dict(overall_metrics),
            'kpis': {
                'attendance_rate': round(attendance_rate, 2),
                'punctuality_rate': round(punctuality_rate, 2),
                'avg_work_hours': round(overall_metrics['avg_work_hours'] or 0, 2),
                'total_overtime': round(overall_metrics['total_overtime'] or 0, 2),
                'working_days': overall_metrics['working_days']
            },
            'top_performers': [dict(row) for row in top_performers]
        }
