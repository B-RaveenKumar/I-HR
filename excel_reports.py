# excel_reports.py
"""
Comprehensive Excel Reporting System for Staff Management Attendance System

This module provides advanced Excel reporting capabilities with:
- Multiple sheet reports
- Charts and graphs
- Formatted tables
- Summary statistics
- Data visualization
"""

import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.chart import BarChart, PieChart, LineChart, Reference
from openpyxl.utils.dataframe import dataframe_to_rows
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
from database import get_db
import io
import base64
from flask import make_response
import calendar
from salary_calculator import SalaryCalculator


class ExcelReportGenerator:
    """Generate comprehensive Excel reports for staff attendance system"""
    
    def __init__(self, generated_by=None):
        self.generated_by = generated_by
        self.header_font = Font(bold=True, size=12, color="FFFFFF")
        self.header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        self.title_font = Font(bold=True, size=16, color="2F5597")
        self.border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
    def _get_salary_data(self, school_id, year, month, department=None):
        """Helper to get salary data from history or calculate on the fly"""
        db = get_db()
        # Try to get from history first
        try:
            query = '''
                SELECT s.id as staff_db_id, s.full_name, s.staff_id, s.bank_name, s.bank_account_number, s.ifsc_code,
                       s.pf_deduction as assigned_pf, s.esi_deduction as assigned_esi,
                       s.basic_salary as profile_basic, s.dearness_allowance as profile_da,
                       sh.net_salary, sh.gross_salary, sh.pf_deduction, sh.esi_deduction, sh.professional_tax, 
                       sh.other_deductions, sh.total_deductions
                FROM staff s
                JOIN salary_history sh ON s.id = sh.staff_db_id
                WHERE s.school_id = ? AND sh.year = ? AND sh.month = ?
            '''
            params = [school_id, year, month]
            if department:
                query += " AND s.department = ?"
                params.append(department)
            query += " ORDER BY s.full_name"
            
            data = db.execute(query, params).fetchall()
            
            if data:
                processed_results = []
                for row in data:
                    r = dict(row)
                    assigned_pf = float(r.get('assigned_pf') or 0)
                    assigned_esi = float(r.get('assigned_esi') or 0)
                    
                    # Force use profile values if they are set
                    if assigned_pf > 0:
                        r['pf_deduction'] = assigned_pf
                    if assigned_esi > 0:
                        r['esi_deduction'] = assigned_esi
                        
                    processed_results.append(r)
                return processed_results
        except Exception as e:
            print(f"Error fetching from salary_history: {e}")
            
        # If no history or table doesn't exist, calculate on the fly
        salary_calculator = SalaryCalculator(school_id=school_id)
        
        staff_columns = [col['name'] for col in db.execute("PRAGMA table_info(staff)").fetchall()]
        where_clause = "school_id = ?"
        params = [school_id]
        if 'is_active' in staff_columns:
            where_clause += " AND COALESCE(is_active, 1) = 1"
        elif 'status' in staff_columns:
            where_clause += " AND LOWER(COALESCE(status, 'active')) = 'active'"
            
        if department:
            where_clause += " AND department = ?"
            params.append(department)
            
        staff_list = db.execute(f'''
            SELECT id, staff_id, full_name, bank_name, bank_account_number, ifsc_code,
                   pf_deduction, esi_deduction, professional_tax, other_deductions,
                   basic_salary, dearness_allowance
            FROM staff 
            WHERE {where_clause}
        ''', params).fetchall()
        
        results = []
        for staff in staff_list:
            res = salary_calculator.calculate_monthly_salary(staff['id'], year, month)
            if res['success']:
                breakdown = res['salary_breakdown']
                earnings = breakdown.get('earnings', {})
                deductions = breakdown.get('deductions', {})
                
                # Use profile values if set, otherwise fallback to calculated
                assigned_pf = float(staff['pf_deduction'] or 0)
                assigned_esi = float(staff['esi_deduction'] or 0)
                assigned_pt = float(staff['professional_tax'] or 0)
                
                results.append({
                    'staff_db_id': staff['id'],
                    'full_name': staff['full_name'],
                    'staff_id': staff['staff_id'],
                    'bank_name': staff['bank_name'],
                    'bank_account_number': staff['bank_account_number'],
                    'ifsc_code': staff['ifsc_code'],
                    'net_salary': breakdown.get('net_salary', 0),
                    'gross_salary': earnings.get('total_earnings', 0),
                    'pf_deduction': assigned_pf if assigned_pf > 0 else deductions.get('pf_deduction', deductions.get('employee_pf', 0)),
                    'esi_deduction': assigned_esi if assigned_esi > 0 else deductions.get('esi_deduction', 0),
                    'professional_tax': assigned_pt if assigned_pt > 0 else deductions.get('professional_tax', 0),
                    'absent_deduction': deductions.get('absent_deduction', 0),
                    'late_penalty': deductions.get('late_arrival_penalty', 0),
                    'early_penalty': deductions.get('early_departure_penalty', 0),
                    'single_punch_penalty': deductions.get('single_punch_penalty', 0),
                    'manual_deduction': breakdown.get('manual_deduction', 0),
                    'other_deductions': deductions.get('other_deductions', 0),
                    'total_deductions': deductions.get('total_deductions', 0),
                    'assigned_pf': assigned_pf,
                    'assigned_esi': assigned_esi,
                    'profile_basic': float(staff['basic_salary'] or 0),
                    'profile_da': float(staff['dearness_allowance'] or 0),
                    'pf_wage': deductions.get('pf_wage', 0),
                    'employer_epf': deductions.get('employer_epf', 0),
                    'eps': deductions.get('eps', 0),
                    'edli': deductions.get('edli', 0),
                    'admin_charges': deductions.get('admin_charges', 0)
                })
        return results
        
    def create_staff_attendance_report(self, school_id, start_date, end_date, department=None):
        """Create comprehensive staff attendance report"""
        wb = openpyxl.Workbook()
        
        # Remove default sheet
        wb.remove(wb.active)
        
        # Create multiple sheets
        self._create_summary_sheet(wb, school_id, start_date, end_date)
        self._create_detailed_attendance_sheet(wb, school_id, start_date, end_date)
        self._create_staff_profile_sheet(wb, school_id)
        self._create_department_analysis_sheet(wb, school_id, start_date, end_date)
        self._create_charts_sheet(wb, school_id, start_date, end_date)
        
        return self._save_workbook_to_response(wb, f"Staff_Attendance_Report_{start_date}_to_{end_date}.xlsx")
    
    def create_individual_staff_report(self, staff_id, start_date, end_date, department=None):
        """Create individual staff attendance report"""
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        
        self._create_individual_summary_sheet(wb, staff_id, start_date, end_date)
        self._create_individual_detailed_sheet(wb, staff_id, start_date, end_date)
        self._create_individual_charts_sheet(wb, staff_id, start_date, end_date)
        
        db = get_db()
        staff = db.execute('SELECT full_name FROM staff WHERE id = ?', (staff_id,)).fetchone()
        staff_name = staff['full_name'].replace(' ', '_') if staff else 'Unknown'
        
        return self._save_workbook_to_response(wb, f"Individual_Report_{staff_name}_{start_date}_to_{end_date}.xlsx")
    
    def create_company_report(self, start_date, end_date, department=None):
        """Create company-wide report across all schools"""
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        
        self._create_company_summary_sheet(wb, start_date, end_date)
        self._create_school_comparison_sheet(wb, start_date, end_date)
        self._create_company_charts_sheet(wb, start_date, end_date)
        
        return self._save_workbook_to_response(wb, f"Company_Report_{start_date}_to_{end_date}.xlsx")
    
    def create_monthly_report(self, school_id, year, month, department=None):
        """Create monthly attendance report with individual staff records"""
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
        
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        
        # Create Staff Records sheet FIRST (main data users want to see)
        self._create_monthly_staff_records_sheet(wb, school_id, year, month, department)
        
        # Create summary sheets
        self._create_monthly_summary_sheet(wb, school_id, year, month, department)
        self._create_monthly_calendar_sheet(wb, school_id, year, month, department)
        self._create_monthly_trends_sheet(wb, school_id, year, month, department)
        
        return self._save_workbook_to_response(wb, f"Monthly_Report_{year}_{month:02d}.xlsx")

    def create_attendance_trends_report(self, school_id, year, department=None):
        """Create a comprehensive attendance trends report for the year"""
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        
        self._create_yearly_summary_trends_sheet(wb, school_id, year, department)
        self._create_department_trends_sheet(wb, school_id, year, department)
        self._create_monthly_comparison_sheet(wb, school_id, year, department)
        
        return self._save_workbook_to_response(wb, f"Attendance_Trends_Report_{year}.xlsx")

    def create_student_performance_report(self, school_id, student_class=None):
        """Create a summary of student academic performance based on admission data"""
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        
        self._create_student_academic_summary_sheet(wb, school_id, student_class)
        self._create_student_toppers_sheet(wb, school_id, student_class)
        
        filename = f"Student_Performance_Report_{student_class if student_class and student_class != 'all' else 'All_Classes'}.xlsx"
        return self._save_workbook_to_response(wb, filename)

    def create_fee_collection_report(self, school_id, student_class=None):
        """Create a comprehensive fee collection vs outstanding report"""
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        
        self._create_fee_summary_sheet(wb, school_id, student_class)
        self._create_fee_defaulters_sheet(wb, school_id, student_class)
        self._create_fee_type_analysis_sheet(wb, school_id)
        
        filename = f"Fee_Collection_Report_{datetime.now().strftime('%Y%m%d')}.xlsx"
        return self._save_workbook_to_response(wb, filename)

    def create_staff_compliance_report(self, school_id, department=None):
        """Create a comprehensive staff document and profile compliance report"""
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        
        self._create_staff_compliance_summary_sheet(wb, school_id, department)
        self._create_staff_missing_info_sheet(wb, school_id, department)
        
        filename = f"Staff_Compliance_Report_{datetime.now().strftime('%Y%m%d')}.xlsx"
        return self._save_workbook_to_response(wb, filename)

    def create_logistics_report(self, school_id, student_class=None):
        """Create a comprehensive logistics report (Hostel vs Day Scholar)"""
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        
        self._create_logistics_summary_sheet(wb, school_id, student_class)
        self._create_logistics_directory_sheet(wb, school_id, student_class)
        
        filename = f"Student_Logistics_Report_{datetime.now().strftime('%Y%m%d')}.xlsx"
        return self._save_workbook_to_response(wb, filename)

    def create_salary_increment_report(self, school_id, department=None):
        """Create a comprehensive staff salary increment history report"""
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        
        self._create_salary_history_sheet(wb, school_id, department)
        self._create_salary_stats_sheet(wb, school_id)
        
        filename = f"Staff_Salary_Increment_Report_{datetime.now().strftime('%Y%m%d')}.xlsx"
        return self._save_workbook_to_response(wb, filename)

    def create_audit_log_report(self, school_id, department=None):
        """Create a comprehensive administrative audit log report"""
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        
        self._create_audit_trail_sheet(wb, school_id, department)
        
        filename = f"Admin_Audit_Log_Report_{datetime.now().strftime('%Y%m%d')}.xlsx"
        return self._save_workbook_to_response(wb, filename)

    def create_overtime_report(self, school_id, year, month, department=None):
        """Create comprehensive overtime report with individual staff overtime data"""
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
        
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        
        # Create Overtime Records sheet FIRST (main data users want to see)
        self._create_overtime_records_sheet(wb, school_id, year, month, department)
        
        # Create summary sheets
        self._create_overtime_summary_sheet(wb, school_id, year, month, department)
        self._create_overtime_trends_sheet(wb, school_id, year, month, department)
        
        return self._save_workbook_to_response(wb, f"Overtime_Report_{year}_{month:02d}.xlsx")
    
    def create_leave_report(self, school_id, year, month=None, department=None):
        """Create comprehensive leave report"""
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        
        self._create_leave_summary_sheet(wb, school_id, year, month, department)
        self._create_leave_details_sheet(wb, school_id, year, month)
        
        month_suffix = f"_{month:02d}" if month else ""
        return self._save_workbook_to_response(wb, f"Leave_Report_{year}{month_suffix}.xlsx")

    def create_late_early_report(self, school_id, year, month, department=None):
        """Create report for Late Entry and Early Exit"""
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        
        self._create_late_entry_sheet(wb, school_id, year, month, department)
        self._create_early_exit_sheet(wb, school_id, year, month, department)
        
        return self._save_workbook_to_response(wb, f"Late_Early_Report_{year}_{month:02d}.xlsx")

    def create_shift_wise_attendance_report(self, school_id, year, month, department=None):
        """Create Shift-Wise Attendance Summary"""
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        
        self._create_shift_attendance_summary_sheet(wb, school_id, year, month, department)
        
        return self._save_workbook_to_response(wb, f"Shift_Wise_Attendance_{year}_{month:02d}.xlsx")

    def create_absenteeism_report(self, school_id, year, month, department=None):
        """Create Absenteeism Frequency Report"""
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        
        self._create_absenteeism_analysis_sheet(wb, school_id, year, month, department)
        
        return self._save_workbook_to_response(wb, f"Absenteeism_Analysis_{year}_{month:02d}.xlsx")

    def create_biometric_log_report(self, school_id, date, department=None):
        """Create Detailed Biometric Punch Log Report"""
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        
        self._create_biometric_punch_log_sheet(wb, school_id, date, department)
        
        return self._save_workbook_to_response(wb, f"Biometric_Punch_Logs_{date}.xlsx")

    def create_staff_profile_report(self, school_id, department=None):
        """Create comprehensive staff profile report"""
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        
        self._create_staff_profile_sheet(wb, school_id)
        
        return self._save_workbook_to_response(wb, f"Staff_Profile_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")

    def create_bank_advice_report(self, school_id, year, month, department=None):
        """Create Bank Advice (Salary Transfer) Report"""
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        
        self._create_bank_advice_sheet(wb, school_id, year, month, department)
        
        return self._save_workbook_to_response(wb, f"Bank_Advice_{year}_{month:02d}.xlsx")

    def create_statutory_compliance_report(self, school_id, year, month, department=None):
        """Create Statutory Compliance (PF & ESI) Report"""
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        
        self._create_statutory_compliance_sheet(wb, school_id, year, month, department)
        
        return self._save_workbook_to_response(wb, f"PF_ESI_Compliance_{year}_{month:02d}.xlsx")

    def create_deduction_analysis_report(self, school_id, year, month, department=None):
        """Create Deduction Analysis Report"""
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        
        self._create_deduction_analysis_sheet(wb, school_id, year, month, department)
        
        return self._save_workbook_to_response(wb, f"Deduction_Analysis_{year}_{month:02d}.xlsx")

    def create_salary_structure_report(self, school_id, department=None):
        """Create Staff Salary Structure (CTC) Report"""
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        
        self._create_salary_structure_sheet(wb, school_id, department)
        
        return self._save_workbook_to_response(wb, f"Salary_Structure_Report_{datetime.now().strftime('%Y%m%d')}.xlsx")

    def create_leave_report(self, school_id, year, month=None, department=None):
        """Create comprehensive leave applications report"""
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        ws = wb.create_sheet("Leave Reports")
        
        # Title
        ws['A1'] = "Staff Leave Applications Report"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:J1')
        if self.generated_by:
            ws['A2'] = f"Generated by: {self.generated_by}"
        
        # Headers
        headers = ['Staff ID', 'Name', 'Department', 'Type', 'Start Date', 'End Date', 'Days', 'Reason', 'Status', 'Applied At', 'Processed By', 'Processed At', 'Admin Remarks']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = Alignment(horizontal='center')
        
        # Query data
        db = get_db()
        query = '''
            SELECT s.staff_id, s.full_name, s.department, l.leave_type, l.start_date, l.end_date, 
                   l.reason, l.status, l.applied_at, l.processed_at, l.admin_remarks, adm.full_name as admin_name
            FROM leave_applications l
            JOIN staff s ON l.staff_id = s.id
            LEFT JOIN admins adm ON l.processed_by = adm.id
            WHERE l.school_id = ? AND strftime('%Y', l.start_date) = ?
        '''
        params = [school_id, str(year)]
        if month:
            query += " AND strftime('%m', l.start_date) = ?"
            params.append(f"{month:02d}")
        
        query += " ORDER BY l.start_date DESC"
        data = db.execute(query, params).fetchall()
        
        for row, record in enumerate(data, 4):
            ws.cell(row=row, column=1, value=record['staff_id'])
            ws.cell(row=row, column=2, value=record['full_name'])
            ws.cell(row=row, column=3, value=record['department'] or 'N/A')
            ws.cell(row=row, column=4, value=record['leave_type'])
            ws.cell(row=row, column=5, value=record['start_date'])
            ws.cell(row=row, column=6, value=record['end_date'])
            
            # Calculate days
            try:
                start = record['start_date']
                end = record['end_date']
                if isinstance(start, str):
                    start = datetime.strptime(start, '%Y-%m-%d')
                if isinstance(end, str):
                    end = datetime.strptime(end, '%Y-%m-%d')
                days = (end - start).days + 1
            except:
                days = 'N/A'
            ws.cell(row=row, column=7, value=days)
            
            ws.cell(row=row, column=8, value=record['reason'] or '')
            ws.cell(row=row, column=9, value=record['status'].title())
            ws.cell(row=row, column=10, value=str(record['applied_at'])[:10] if record['applied_at'] else '')
            ws.cell(row=row, column=11, value=record['admin_name'] or 'N/A')
            ws.cell(row=row, column=12, value=str(record['processed_at'])[:10] if record['processed_at'] else 'N/A')
            ws.cell(row=row, column=13, value=record['admin_remarks'] or '')
            
        # Format columns
        column_widths = [12, 20, 15, 10, 12, 12, 8, 30, 12, 12, 20, 12, 30]
        for col, width in enumerate(column_widths, 1):
            ws.column_dimensions[chr(64 + col) if col <= 26 else 'A' + chr(64 + col - 26)].width = width
            
        for row in range(3, len(data) + 4):
            for col in range(1, 14):
                ws.cell(row=row, column=col).border = self.border

        filename = f"Leave_Report_{year}" + (f"_{month:02d}" if month else "") + ".xlsx"
        return self._save_workbook_to_response(wb, filename)

    def create_od_report(self, school_id, year, month=None, department=None):
        """Create comprehensive On-Duty (OD) applications report"""
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        ws = wb.create_sheet("OD Reports")
        
        ws['A1'] = "Staff On-Duty (OD) Applications Report"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:J1')
        if self.generated_by:
            ws['A2'] = f"Generated by: {self.generated_by}"
        
        headers = ['Staff ID', 'Name', 'Department', 'Duty Type', 'Start Date', 'End Date', 'Location', 'Purpose', 'Status', 'Applied At', 'Processed By', 'Processed At', 'Admin Remarks']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = Alignment(horizontal='center')
        
        db = get_db()
        query = '''
            SELECT s.staff_id, s.full_name, s.department, o.duty_type, o.start_date, o.end_date, 
                   o.location, o.purpose, o.status, o.applied_at, o.processed_at, o.admin_remarks, adm.full_name as admin_name
            FROM on_duty_applications o
            JOIN staff s ON o.staff_id = s.id
            LEFT JOIN admins adm ON o.processed_by = adm.id
            WHERE o.school_id = ? AND strftime('%Y', o.start_date) = ?
        '''
        params = [school_id, str(year)]
        if month:
            query += " AND strftime('%m', o.start_date) = ?"
            params.append(f"{month:02d}")
        
        query += " ORDER BY o.start_date DESC"
        data = db.execute(query, params).fetchall()
        
        for row, record in enumerate(data, 4):
            ws.cell(row=row, column=1, value=record['staff_id'])
            ws.cell(row=row, column=2, value=record['full_name'])
            ws.cell(row=row, column=3, value=record['department'] or 'N/A')
            ws.cell(row=row, column=4, value=record['duty_type'])
            ws.cell(row=row, column=5, value=record['start_date'])
            ws.cell(row=row, column=6, value=record['end_date'])
            ws.cell(row=row, column=7, value=record['location'] or 'N/A')
            ws.cell(row=row, column=8, value=record['purpose'] or '')
            ws.cell(row=row, column=9, value=record['status'].title())
            ws.cell(row=row, column=10, value=str(record['applied_at'])[:10] if record['applied_at'] else '')
            ws.cell(row=row, column=11, value=record['admin_name'] or 'N/A')
            ws.cell(row=row, column=12, value=str(record['processed_at'])[:10] if record['processed_at'] else 'N/A')
            ws.cell(row=row, column=13, value=record['admin_remarks'] or '')
            
        column_widths = [12, 20, 15, 15, 12, 12, 20, 30, 12, 12, 20, 12, 30]
        for col, width in enumerate(column_widths, 1):
            ws.column_dimensions[chr(64 + col) if col <= 26 else 'A' + chr(64 + col - 26)].width = width
            
        for row in range(3, len(data) + 4):
            for col in range(1, 14):
                ws.cell(row=row, column=col).border = self.border

        filename = f"OD_Report_{year}" + (f"_{month:02d}" if month else "") + ".xlsx"
        return self._save_workbook_to_response(wb, filename)

    def create_permission_report(self, school_id, year, month=None, department=None):
        """Create comprehensive permission applications report"""
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        ws = wb.create_sheet("Permission Reports")
        
        ws['A1'] = "Staff Permission Applications Report"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:J1')
        if self.generated_by:
            ws['A2'] = f"Generated by: {self.generated_by}"
        
        headers = ['Staff ID', 'Name', 'Department', 'Type', 'Date', 'Start Time', 'End Time', 'Duration', 'Status', 'Applied At', 'Processed By', 'Processed At', 'Admin Remarks']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = Alignment(horizontal='center')
        
        db = get_db()
        query = '''
            SELECT s.staff_id, s.full_name, s.department, p.permission_type, p.permission_date, 
                   p.start_time, p.end_time, p.duration_hours, p.status, p.applied_at, p.processed_at, p.admin_remarks, adm.full_name as admin_name
            FROM permission_applications p
            JOIN staff s ON p.staff_id = s.id
            LEFT JOIN admins adm ON p.processed_by = adm.id
            WHERE p.school_id = ? AND strftime('%Y', p.permission_date) = ?
        '''
        params = [school_id, str(year)]
        if month:
            query += " AND strftime('%m', p.permission_date) = ?"
            params.append(f"{month:02d}")
        
        query += " ORDER BY p.permission_date DESC"
        data = db.execute(query, params).fetchall()
        
        for row, record in enumerate(data, 4):
            ws.cell(row=row, column=1, value=record['staff_id'])
            ws.cell(row=row, column=2, value=record['full_name'])
            ws.cell(row=row, column=3, value=record['department'] or 'N/A')
            ws.cell(row=row, column=4, value=record['permission_type'])
            ws.cell(row=row, column=5, value=record['permission_date'])
            ws.cell(row=row, column=6, value=record['start_time'])
            ws.cell(row=row, column=7, value=record['end_time'])
            ws.cell(row=row, column=8, value=f"{record['duration_hours']}h" if record['duration_hours'] else 'N/A')
            ws.cell(row=row, column=9, value=record['status'].title())
            ws.cell(row=row, column=10, value=str(record['applied_at'])[:10] if record['applied_at'] else '')
            ws.cell(row=row, column=11, value=record['admin_name'] or 'N/A')
            ws.cell(row=row, column=12, value=str(record['processed_at'])[:10] if record['processed_at'] else 'N/A')
            ws.cell(row=row, column=13, value=record['admin_remarks'] or '')
            
        column_widths = [12, 20, 15, 15, 12, 10, 10, 10, 12, 12, 20, 12, 30]
        for col, width in enumerate(column_widths, 1):
            ws.column_dimensions[chr(64 + col) if col <= 26 else 'A' + chr(64 + col - 26)].width = width
            
        for row in range(3, len(data) + 4):
            for col in range(1, 14):
                ws.cell(row=row, column=col).border = self.border

        filename = f"Permission_Report_{year}" + (f"_{month:02d}" if month else "") + ".xlsx"
        return self._save_workbook_to_response(wb, filename)
    
    def _create_summary_sheet(self, wb, school_id, start_date, end_date):
        """Create summary sheet with key metrics"""
        ws = wb.create_sheet("Summary")
        
        # Title
        ws['A1'] = "Staff Attendance Summary Report"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:F1')
        
        # Report details
        ws['A3'] = f"Report Period: {start_date} to {end_date}"
        ws['A4'] = f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        if self.generated_by:
            ws['A5'] = f"Generated by: {self.generated_by}"
            current_info_row = 6
        else:
            current_info_row = 5
        
        db = get_db()
        
        # Get school info
        school = db.execute('SELECT name FROM schools WHERE id = ?', (school_id,)).fetchone()
        ws[f'A{current_info_row}'] = f"School: {school['name'] if school else 'Unknown'}"
        
        # Summary statistics
        ws['A7'] = "Summary Statistics"
        ws['A7'].font = Font(bold=True, size=14)
        
        # Headers
        headers = ['Metric', 'Value']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=8, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = Alignment(horizontal='center')
        
        # Calculate metrics
        total_staff = db.execute('SELECT COUNT(*) as count FROM staff WHERE school_id = ?', (school_id,)).fetchone()['count']
        
        total_attendance_records = db.execute('''
            SELECT COUNT(*) as count FROM attendance 
            WHERE school_id = ? AND date BETWEEN ? AND ?
        ''', (school_id, start_date, end_date)).fetchone()['count']
        
        present_days = db.execute('''
            SELECT COUNT(*) as count FROM attendance 
            WHERE school_id = ? AND date BETWEEN ? AND ? AND status IN ('present', 'late', 'on_duty')
        ''', (school_id, start_date, end_date)).fetchone()['count']
        
        absent_days = db.execute('''
            SELECT COUNT(*) as count FROM attendance 
            WHERE school_id = ? AND date BETWEEN ? AND ? AND status = 'absent'
        ''', (school_id, start_date, end_date)).fetchone()['count']
        
        late_arrivals = db.execute('''
            SELECT COUNT(*) as count FROM attendance 
            WHERE school_id = ? AND date BETWEEN ? AND ? AND status = 'late'
        ''', (school_id, start_date, end_date)).fetchone()['count']
        
        # Add metrics to sheet
        metrics = [
            ('Total Staff', total_staff),
            ('Total Attendance Records', total_attendance_records),
            ('Present Days', present_days),
            ('Absent Days', absent_days),
            ('Late Arrivals', late_arrivals),
            ('Attendance Rate', f"{(present_days / total_attendance_records * 100):.1f}%" if total_attendance_records > 0 else "0%")
        ]
        
        for row, (metric, value) in enumerate(metrics, 9):
            ws.cell(row=row, column=1, value=metric)
            ws.cell(row=row, column=2, value=value)
        
        # Format columns
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 15
        
        # Add borders
        for row in range(8, 15):
            for col in range(1, 3):
                ws.cell(row=row, column=col).border = self.border
    
    def _create_detailed_attendance_sheet(self, wb, school_id, start_date, end_date):
        """Create detailed attendance sheet"""
        ws = wb.create_sheet("Detailed Attendance")
        
        # Title
        ws['A1'] = "Detailed Attendance Records"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:H1')
        
        # Headers
        headers = ['Staff ID', 'Full Name', 'Department', 'Date', 'Time In', 'Time Out', 'Status', 'Notes']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = Alignment(horizontal='center')
        
        # Get data
        db = get_db()
        attendance_data = db.execute('''
            SELECT s.staff_id, s.full_name, s.department, a.date, a.time_in, a.time_out, a.status, a.notes
            FROM attendance a
            JOIN staff s ON a.staff_id = s.id
            WHERE a.school_id = ? AND a.date BETWEEN ? AND ?
            ORDER BY a.date DESC, s.full_name
        ''', (school_id, start_date, end_date)).fetchall()
        
        # Add data
        for row, record in enumerate(attendance_data, 4):
            ws.cell(row=row, column=1, value=record['staff_id'])
            ws.cell(row=row, column=2, value=record['full_name'])
            ws.cell(row=row, column=3, value=record['department'] or 'N/A')
            ws.cell(row=row, column=4, value=record['date'])
            ws.cell(row=row, column=5, value=record['time_in'])
            ws.cell(row=row, column=6, value=record['time_out'])
            ws.cell(row=row, column=7, value=record['status'].title())
            ws.cell(row=row, column=8, value=record['notes'] or '')
        
        # Format columns
        column_widths = [12, 20, 15, 12, 10, 10, 12, 30]
        for col, width in enumerate(column_widths, 1):
            ws.column_dimensions[chr(64 + col)].width = width
        
        # Add borders to all data
        for row in range(3, len(attendance_data) + 4):
            for col in range(1, 9):
                ws.cell(row=row, column=col).border = self.border
    
    def _create_yearly_summary_trends_sheet(self, wb, school_id, year, department=None):
        """Create a summary sheet for yearly attendance trends"""
        ws = wb.create_sheet("Yearly Summary Trends")
        ws['A1'] = f"Staff Attendance Trend Analytics - {year}"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:F1')
        
        if self.generated_by:
            ws['A2'] = f"Generated by: {self.generated_by} on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            ws.merge_cells('A2:F2')

        db = get_db()
        
        # Monthly attendance statistics for the whole year
        monthly_stats = db.execute('''
            SELECT 
                strftime('%m', date) as month,
                COUNT(CASE WHEN status IN ('present', 'late', 'on_duty') THEN 1 END) as present_count,
                COUNT(CASE WHEN status = 'absent' THEN 1 END) as absent_count,
                COUNT(CASE WHEN status = 'leave' THEN 1 END) as leave_count,
                COUNT(*) as total_count
            FROM attendance
            WHERE school_id = ? AND strftime('%Y', date) = ?
            GROUP BY strftime('%m', date)
            ORDER BY month
        ''', (school_id, str(year))).fetchall()
        
        headers = ['Month', 'Total Staff-Days', 'Present', 'Absent', 'Leave', 'Attendance %']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = Alignment(horizontal='center')
            cell.border = self.border

        import calendar
        row = 5
        months_list = []
        attendance_pcts = []
        
        for m_idx in range(1, 13):
            month_str = f"{m_idx:02d}"
            stat = next((s for s in monthly_stats if s['month'] == month_str), None)
            
            month_name = calendar.month_name[m_idx]
            months_list.append(month_name)
            
            if stat:
                total = stat['total_count']
                present = stat['present_count']
                absent = stat['absent_count']
                leave = stat['leave_count']
                pct = (present / total * 100) if total > 0 else 0
            else:
                total = 0
                present = 0
                absent = 0
                leave = 0
                pct = 0
                
            attendance_pcts.append(pct)
            
            ws.cell(row=row, column=1, value=month_name).border = self.border
            ws.cell(row=row, column=2, value=total).border = self.border
            ws.cell(row=row, column=3, value=present).border = self.border
            ws.cell(row=row, column=4, value=absent).border = self.border
            ws.cell(row=row, column=5, value=leave).border = self.border
            ws.cell(row=row, column=6, value=f"{pct:.1f}%").border = self.border
            row += 1

        # Add a line chart for trends
        chart = LineChart()
        chart.title = "Attendance Trend (Percentage)"
        chart.style = 13
        chart.y_axis.title = 'Percentage'
        chart.x_axis.title = 'Month'
        
        data = Reference(ws, min_col=6, min_row=4, max_row=16)
        cats = Reference(ws, min_col=1, min_row=5, max_row=16)
        chart.add_data(data, titles_from_data=True)
        chart.set_categories(cats)
        
        ws.add_chart(chart, "H4")

    def _create_department_trends_sheet(self, wb, school_id, year):
        """Create department-wise attendance trends sheet"""
        ws = wb.create_sheet("Department Trends")
        ws['A1'] = f"Department-wise Attendance Trends - {year}"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:F1')
        
        db = get_db()
        
        # Get departments
        depts = db.execute('SELECT DISTINCT department FROM staff WHERE school_id = ? AND department IS NOT NULL', (school_id,)).fetchall()
        departments = [d['department'] for d in depts if d['department']]
        
        if not departments:
            ws['A3'] = "No department data available"
            return

        import calendar
        headers = ['Department'] + [calendar.month_name[i] for i in range(1, 13)]
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = Alignment(horizontal='center')
            cell.border = self.border

        row = 4
        for dept in departments:
            ws.cell(row=row, column=1, value=dept).border = self.border
            
            for m_idx in range(1, 13):
                month_str = f"{m_idx:02d}"
                
                stat = db.execute('''
                    SELECT 
                        COUNT(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1 END) as present_count,
                        COUNT(*) as total_count
                    FROM attendance a
                    JOIN staff s ON a.staff_id = s.id
                    WHERE s.school_id = ? AND s.department = ? AND strftime('%Y', a.date) = ? AND strftime('%m', a.date) = ?
                ''', (school_id, dept, str(year), month_str)).fetchone()
                
                pct = (stat['present_count'] / stat['total_count'] * 100) if stat and stat['total_count'] > 0 else 0
                ws.cell(row=row, column=m_idx + 1, value=f"{pct:.1f}%").border = self.border
            
            row += 1

        # Add comparison chart
        chart = BarChart()
        chart.title = "Department Comparison (Current Year)"
        chart.y_axis.title = 'Attendance %'
        chart.x_axis.title = 'Department'
        
        # For simplicity, just chart the average or current month if we wanted, 
        # but let's do a multi-series bar chart for all months
        data = Reference(ws, min_col=2, max_col=13, min_row=3, max_row=row-1)
        cats = Reference(ws, min_col=1, min_row=4, max_row=row-1)
        chart.add_data(data, titles_from_data=True)
        chart.set_categories(cats)
        
        ws.add_chart(chart, f"A{row + 2}")

    def _create_monthly_comparison_sheet(self, wb, school_id, year):
        """Create a month-over-month comparison sheet"""
        ws = wb.create_sheet("MoM Comparison")
        ws['A1'] = f"Month-over-Month Attendance Comparison - {year}"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:F1')
        
        db = get_db()
        
        headers = ['Month', 'Avg Work Hours', 'Late Arrivals', 'Overtime Hours', 'Leaves']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = Alignment(horizontal='center')
            cell.border = self.border

        import calendar
        row = 4
        for m_idx in range(1, 13):
            month_str = f"{m_idx:02d}"
            month_name = calendar.month_name[m_idx]
            
            stats = db.execute('''
                SELECT 
                    AVG(work_hours) as avg_hours,
                    COUNT(CASE WHEN status = 'late' THEN 1 END) as late_count,
                    SUM(overtime_hours) as total_ot,
                    COUNT(CASE WHEN status = 'leave' THEN 1 END) as total_leaves
                FROM attendance
                WHERE school_id = ? AND strftime('%Y', date) = ? AND strftime('%m', date) = ?
            ''', (school_id, str(year), month_str)).fetchone()
            
            ws.cell(row=row, column=1, value=month_name).border = self.border
            ws.cell(row=row, column=2, value=round(stats['avg_hours'] or 0, 2)).border = self.border
            ws.cell(row=row, column=3, value=stats['late_count'] or 0).border = self.border
            ws.cell(row=row, column=4, value=round(stats['total_ot'] or 0, 2)).border = self.border
            ws.cell(row=row, column=5, value=stats['total_leaves'] or 0).border = self.border
            row += 1

    def _create_student_academic_summary_sheet(self, wb, school_id, student_class=None):
        """Create a summary sheet for student academic performance"""
        ws = wb.create_sheet("Academic Summary")
        ws['A1'] = "Student Academic Performance Summary (Admission Basis)"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:G1')
        
        db = get_db()
        query = '''
            SELECT student_id, full_name, class, section, tenth_percentage, twelfth_percentage, skills
            FROM students 
            WHERE school_id = ?
        '''
        params = [school_id]
        if student_class and student_class != 'all':
            query += " AND class = ?"
            params.append(student_class)
            
        students = db.execute(query, params).fetchall()
        
        headers = ['Student ID', 'Full Name', 'Class', 'Sec', '10th %', '12th %', 'Skills/Achievements']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.border = self.border

        row = 4
        for s in students:
            ws.cell(row=row, column=1, value=s['student_id']).border = self.border
            ws.cell(row=row, column=2, value=s['full_name']).border = self.border
            ws.cell(row=row, column=3, value=s['class']).border = self.border
            ws.cell(row=row, column=4, value=s['section']).border = self.border
            ws.cell(row=row, column=5, value=f"{s['tenth_percentage']}%" if s['tenth_percentage'] else "N/A").border = self.border
            ws.cell(row=row, column=6, value=f"{s['twelfth_percentage']}%" if s['twelfth_percentage'] else "N/A").border = self.border
            ws.cell(row=row, column=7, value=s['skills'] or "-").border = self.border
            row += 1

    def _create_student_toppers_sheet(self, wb, school_id, student_class=None):
        """Create a sheet highlighting top performers"""
        ws = wb.create_sheet("Top Performers")
        ws['A1'] = "Top Performers (based on 10th & 12th Marks)"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:F1')
        
        db = get_db()
        
        # 10th Toppers
        ws['A3'] = "Top 10 Students - 10th Standard"
        ws['A3'].font = Font(bold=True, size=12)
        
        query_10th = "SELECT full_name, class, tenth_percentage FROM students WHERE school_id = ? AND tenth_percentage IS NOT NULL"
        params_10th = [school_id]
        if student_class and student_class != 'all':
            query_10th += " AND class = ?"
            params_10th.append(student_class)
        query_10th += " ORDER BY tenth_percentage DESC LIMIT 10"
        
        toppers_10th = db.execute(query_10th, params_10th).fetchall()
        
        row = 5
        ws.cell(row=4, column=1, value="Rank").font = Font(bold=True)
        ws.cell(row=4, column=2, value="Name").font = Font(bold=True)
        ws.cell(row=4, column=3, value="Percentage").font = Font(bold=True)
        
        for idx, s in enumerate(toppers_10th, 1):
            ws.cell(row=row, column=1, value=idx)
            ws.cell(row=row, column=2, value=s['full_name'])
            ws.cell(row=row, column=3, value=f"{s['tenth_percentage']}%")
            row += 1
            
        # 12th Toppers
        row += 2
        ws.cell(row=row, column=1, value="Top 10 Students - 12th Standard").font = Font(bold=True, size=12)
        row += 1
        
        query_12th = "SELECT full_name, class, twelfth_percentage FROM students WHERE school_id = ? AND twelfth_percentage IS NOT NULL"
        params_12th = [school_id]
        if student_class and student_class != 'all':
            query_12th += " AND class = ?"
            params_12th.append(student_class)
        query_12th += " ORDER BY twelfth_percentage DESC LIMIT 10"
        
        toppers_12th = db.execute(query_12th, params_12th).fetchall()
        
        ws.cell(row=row, column=1, value="Rank").font = Font(bold=True)
        ws.cell(row=row, column=2, value="Name").font = Font(bold=True)
        ws.cell(row=row, column=3, value="Percentage").font = Font(bold=True)
        row += 1
        
        for idx, s in enumerate(toppers_12th, 1):
            ws.cell(row=row, column=1, value=idx)
            ws.cell(row=row, column=2, value=s['full_name'])
            ws.cell(row=row, column=3, value=f"{s['twelfth_percentage']}%")
            row += 1

    def _create_fee_summary_sheet(self, wb, school_id, student_class=None):
        """Create a summary sheet for fee collection"""
        ws = wb.create_sheet("Fee Summary")
        ws['A1'] = "Fee Collection vs Outstanding Summary"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:G1')
        
        db = get_db()
        query = '''
            SELECT 
                SUM(amount) as total_assigned,
                SUM(paid_amount) as total_collected,
                SUM(amount - paid_amount) as total_outstanding,
                COUNT(DISTINCT student_db_id) as student_count
            FROM student_fees
            WHERE school_id = ?
        '''
        params = [school_id]
        if student_class and student_class != 'all':
            query = query.replace('FROM student_fees', 'FROM student_fees sf JOIN students s ON sf.student_db_id = s.id')
            query += " AND s.class = ?"
            params.append(student_class)
            
        summary = db.execute(query, params).fetchone()
        
        ws['A3'] = "Metric"
        ws['B3'] = "Value"
        ws['A3'].font = self.header_font
        ws['B3'].font = self.header_font
        ws['A3'].fill = self.header_fill
        ws['B3'].fill = self.header_fill
        
        metrics = [
            ["Total Students with Fees", summary['student_count'] or 0],
            ["Total Amount Assigned", summary['total_assigned'] or 0],
            ["Total Amount Collected", summary['total_collected'] or 0],
            ["Total Amount Outstanding", summary['total_outstanding'] or 0],
            ["Collection Efficiency (%)", f"{(summary['total_collected'] / summary['total_assigned'] * 100):.1f}%" if summary['total_assigned'] and summary['total_assigned'] > 0 else "0%"]
        ]
        
        for row_idx, (metric, val) in enumerate(metrics, 4):
            ws.cell(row=row_idx, column=1, value=metric).border = self.border
            ws.cell(row=row_idx, column=2, value=val).border = self.border

    def _create_fee_defaulters_sheet(self, wb, school_id, student_class=None):
        """Create a sheet listing students with outstanding fees"""
        ws = wb.create_sheet("Defaulters List")
        ws['A1'] = "Fee Defaulters List (Pending Payments)"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:G1')
        
        db = get_db()
        query = '''
            SELECT s.student_id, s.full_name, s.class, s.section, 
                   SUM(sf.amount) as assigned, SUM(sf.paid_amount) as paid, 
                   SUM(sf.amount - sf.paid_amount) as outstanding
            FROM student_fees sf
            JOIN students s ON sf.student_db_id = s.id
            WHERE sf.school_id = ? AND sf.status != 'paid'
        '''
        params = [school_id]
        if student_class and student_class != 'all':
            query += " AND s.class = ?"
            params.append(student_class)
        query += " GROUP BY s.id HAVING outstanding > 0 ORDER BY outstanding DESC"
        
        defaulters = db.execute(query, params).fetchall()
        
        headers = ['Student ID', 'Full Name', 'Class', 'Sec', 'Assigned', 'Paid', 'Outstanding']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.border = self.border

        row = 4
        for d in defaulters:
            ws.cell(row=row, column=1, value=d['student_id']).border = self.border
            ws.cell(row=row, column=2, value=d['full_name']).border = self.border
            ws.cell(row=row, column=3, value=d['class']).border = self.border
            ws.cell(row=row, column=4, value=d['section']).border = self.border
            ws.cell(row=row, column=5, value=d['assigned']).border = self.border
            ws.cell(row=row, column=6, value=d['paid']).border = self.border
            ws.cell(row=row, column=7, value=d['outstanding']).border = self.border
            row += 1

    def _create_fee_type_analysis_sheet(self, wb, school_id):
        """Create a sheet analyzing collection by fee type"""
        ws = wb.create_sheet("Fee Type Analysis")
        ws['A1'] = "Collection Analysis by Fee Type"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:F1')
        
        db = get_db()
        # Note: assuming fee_types table exists based on foreign keys in student_fees
        query = '''
            SELECT ft.name, SUM(sf.amount) as assigned, SUM(sf.paid_amount) as paid
            FROM student_fees sf
            JOIN fee_types ft ON sf.fee_type_id = ft.id
            WHERE sf.school_id = ?
            GROUP BY ft.id
        '''
        analysis = db.execute(query, (school_id,)).fetchall()
        
        headers = ['Fee Type', 'Total Assigned', 'Total Collected', 'Outstanding', 'Efficiency %']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.border = self.border

        row = 4
        for a in analysis:
            outstanding = a['assigned'] - a['paid']
            efficiency = (a['paid'] / a['assigned'] * 100) if a['assigned'] > 0 else 0
            
            ws.cell(row=row, column=1, value=a['name']).border = self.border
            ws.cell(row=row, column=2, value=a['assigned']).border = self.border
            ws.cell(row=row, column=3, value=a['paid']).border = self.border
            ws.cell(row=row, column=4, value=outstanding).border = self.border
            ws.cell(row=row, column=5, value=f"{efficiency:.1f}%").border = self.border
            row += 1

    def _create_staff_compliance_summary_sheet(self, wb, school_id, department=None):
        """Create a summary sheet for staff profile compliance"""
        ws = wb.create_sheet("Compliance Summary")
        ws['A1'] = "Staff Profile & Document Compliance Summary"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:G1')
        
        db = get_db()
        staff_data = db.execute('''
            SELECT 
                full_name, department, pan_number, aadhar_number, 
                bank_account_number, phone, email, photo_data
            FROM staff 
            WHERE school_id = ? AND is_active = 1
        ''', (school_id,)).fetchall()
        
        total_staff = len(staff_data)
        if total_staff == 0:
            ws['A3'] = "No active staff found"
            return

        # Calculate counts
        pan_count = sum(1 for s in staff_data if s['pan_number'])
        aadhar_count = sum(1 for s in staff_data if s['aadhar_number'])
        bank_count = sum(1 for s in staff_data if s['bank_account_number'])
        photo_count = sum(1 for s in staff_data if s['photo_data'])
        contact_count = sum(1 for s in staff_data if s['phone'] or s['email'])
        
        ws['A3'] = "Compliance Category"
        ws['B3'] = "Completed"
        ws['C3'] = "Pending"
        ws['D3'] = "Compliance %"
        
        for col in range(1, 5):
            ws.cell(row=3, column=col).font = self.header_font
            ws.cell(row=3, column=col).fill = self.header_fill
            ws.cell(row=3, column=col).border = self.border

        categories = [
            ["PAN Card Details", pan_count],
            ["Aadhar Card Details", aadhar_count],
            ["Bank Account Info", bank_count],
            ["Profile Photo", photo_count],
            ["Contact Info (Phone/Email)", contact_count]
        ]
        
        row = 4
        for cat, count in categories:
            pending = total_staff - count
            pct = (count / total_staff * 100)
            
            ws.cell(row=row, column=1, value=cat).border = self.border
            ws.cell(row=row, column=2, value=count).border = self.border
            ws.cell(row=row, column=3, value=pending).border = self.border
            ws.cell(row=row, column=4, value=f"{pct:.1f}%").border = self.border
            row += 1

        # Add total
        ws.cell(row=row, column=1, value="Total Active Staff").font = Font(bold=True)
        ws.cell(row=row, column=2, value=total_staff).font = Font(bold=True)

    def _create_staff_missing_info_sheet(self, wb, school_id, department=None):
        """Create a detailed sheet showing exactly what's missing for each staff member"""
        ws = wb.create_sheet("Missing Info Details")
        ws['A1'] = "Detailed Missing Information by Staff Member"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:G1')
        
        db = get_db()
        staff_data = db.execute('''
            SELECT staff_id, full_name, department, pan_number, aadhar_number, 
                   bank_account_number, phone, email, photo_data
            FROM staff 
            WHERE school_id = ? AND is_active = 1
            ORDER BY department, full_name
        ''', (school_id,)).fetchall()
        
        headers = ['Staff ID', 'Name', 'Department', 'Missing Info']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.border = self.border

        row = 4
        for s in staff_data:
            missing = []
            if not s['pan_number']: missing.append("PAN")
            if not s['aadhar_number']: missing.append("Aadhar")
            if not s['bank_account_number']: missing.append("Bank Details")
            if not s['photo_data']: missing.append("Photo")
            if not s['phone'] and not s['email']: missing.append("Contact Info")
            
            if missing:
                ws.cell(row=row, column=1, value=s['staff_id']).border = self.border
                ws.cell(row=row, column=2, value=s['full_name']).border = self.border
                ws.cell(row=row, column=3, value=s['department']).border = self.border
                ws.cell(row=row, column=4, value=", ".join(missing)).border = self.border
                
                # Highlight if many items missing
                if len(missing) >= 3:
                    ws.cell(row=row, column=4).fill = PatternFill(start_color="FFCCCC", end_color="FFCCCC", fill_type="solid")
                
                row += 1

        if row == 4:
            ws['A4'] = "All staff profiles are 100% complete!"
            ws.merge_cells('A4:D4')
            ws['A4'].alignment = Alignment(horizontal='center')

    def _create_logistics_summary_sheet(self, wb, school_id, student_class=None):
        """Create a summary sheet for student logistics (Hostel vs Day Scholar)"""
        ws = wb.create_sheet("Logistics Summary")
        ws['A1'] = "Student Logistics Distribution Summary"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:F1')
        
        db = get_db()
        query = '''
            SELECT class, student_type, COUNT(*) as count
            FROM students
            WHERE school_id = ?
        '''
        params = [school_id]
        if student_class and student_class != 'all':
            query += " AND class = ?"
            params.append(student_class)
        query += " GROUP BY class, student_type ORDER BY class"
        
        stats = db.execute(query, params).fetchall()
        
        headers = ['Class', 'Day Scholar', 'Hosteller', 'Total']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.border = self.border

        # Group data by class
        class_data = {}
        for s in stats:
            cls = s['class']
            if cls not in class_data:
                class_data[cls] = {'Day Scholar': 0, 'Hostel': 0}
            
            # Map database types to headers
            stype = s['student_type']
            if stype in ['Hostel', 'Hosteller']:
                class_data[cls]['Hostel'] += s['count']
            else:
                class_data[cls]['Day Scholar'] += s['count']

        row = 4
        for cls, counts in class_data.items():
            total = counts['Day Scholar'] + counts['Hostel']
            ws.cell(row=row, column=1, value=cls).border = self.border
            ws.cell(row=row, column=2, value=counts['Day Scholar']).border = self.border
            ws.cell(row=row, column=3, value=counts['Hostel']).border = self.border
            ws.cell(row=row, column=4, value=total).border = self.border
            row += 1

    def _create_logistics_directory_sheet(self, wb, school_id, student_class=None):
        """Create a detailed directory sheet for logistics planning"""
        ws = wb.create_sheet("Logistics Directory")
        ws['A1'] = "Detailed Student Logistics Directory"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:G1')
        
        db = get_db()
        query = '''
            SELECT student_id, full_name, class, section, student_type, gender, address
            FROM students
            WHERE school_id = ?
        '''
        params = [school_id]
        if student_class and student_class != 'all':
            query += " AND class = ?"
            params.append(student_class)
        query += " ORDER BY student_type, class, full_name"
        
        students = db.execute(query, params).fetchall()
        
        headers = ['ID', 'Name', 'Class', 'Sec', 'Type', 'Gender', 'Address']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.border = self.border

        row = 4
        for s in students:
            ws.cell(row=row, column=1, value=s['student_id']).border = self.border
            ws.cell(row=row, column=2, value=s['full_name']).border = self.border
            ws.cell(row=row, column=3, value=s['class']).border = self.border
            ws.cell(row=row, column=4, value=s['section']).border = self.border
            ws.cell(row=row, column=5, value=s['student_type']).border = self.border
            ws.cell(row=row, column=6, value=s['gender']).border = self.border
            ws.cell(row=row, column=7, value=s['address'] or "-").border = self.border
            
            # Color code by type
            if s['student_type'] in ['Hostel', 'Hosteller']:
                ws.cell(row=row, column=5).fill = PatternFill(start_color="E6F3FF", end_color="E6F3FF", fill_type="solid")
            
            row += 1

    def _create_salary_history_sheet(self, wb, school_id, department=None):
        """Create a sheet showing chronological salary history for staff"""
        ws = wb.create_sheet("Increment History")
        ws['A1'] = "Staff Salary Increment History"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:H1')
        
        db = get_db()
        history = db.execute('''
            SELECT s.staff_id, s.full_name, s.department, 
                   sh.previous_salary, sh.new_salary, sh.increment_amount, 
                   sh.change_date, sh.reason
            FROM staff_salary_history sh
            JOIN staff s ON sh.staff_id = s.id
            WHERE sh.school_id = ?
            ORDER BY sh.change_date DESC, s.full_name
        ''', (school_id,)).fetchall()
        
        headers = ['Staff ID', 'Name', 'Department', 'Prev Salary', 'New Salary', 'Increment', 'Date', 'Reason']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.border = self.border

        row = 4
        for h in history:
            ws.cell(row=row, column=1, value=h['staff_id']).border = self.border
            ws.cell(row=row, column=2, value=h['full_name']).border = self.border
            ws.cell(row=row, column=3, value=h['department']).border = self.border
            ws.cell(row=row, column=4, value=h['previous_salary']).border = self.border
            ws.cell(row=row, column=5, value=h['new_salary']).border = self.border
            ws.cell(row=row, column=6, value=h['increment_amount']).border = self.border
            ws.cell(row=row, column=7, value=h['change_date']).border = self.border
            ws.cell(row=row, column=8, value=h['reason']).border = self.border
            
            # Highlight positive increments in green
            if h['increment_amount'] > 0:
                ws.cell(row=row, column=6).fill = PatternFill(start_color="CCFFCC", end_color="CCFFCC", fill_type="solid")
            
            row += 1

    def _create_salary_stats_sheet(self, wb, school_id):
        """Create a sheet showing statistical overview of salary distribution"""
        ws = wb.create_sheet("Salary Overview")
        ws['A1'] = "Staff Salary Overview & Statistics"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:G1')
        
        db = get_db()
        stats = db.execute('''
            SELECT 
                COUNT(*) as total_staff,
                SUM(basic_salary) as total_monthly_outflow,
                AVG(basic_salary) as avg_salary,
                MIN(basic_salary) as min_salary,
                MAX(basic_salary) as max_salary
            FROM staff
            WHERE school_id = ? AND is_active = 1
        ''', (school_id,)).fetchone()
        
        ws['A3'] = "Metric"
        ws['B3'] = "Value"
        ws['A3'].font = self.header_font
        ws['B3'].font = self.header_font
        ws['A3'].fill = self.header_fill
        ws['B3'].fill = self.header_fill
        
        data = [
            ["Total Active Staff", stats['total_staff']],
            ["Total Monthly Basic Salary Outflow", stats['total_monthly_outflow']],
            ["Average Monthly Salary", round(stats['avg_salary'] or 0, 2)],
            ["Minimum Monthly Salary", stats['min_salary']],
            ["Maximum Monthly Salary", stats['max_salary']]
        ]
        
        for idx, (m, v) in enumerate(data, 4):
            ws.cell(row=idx, column=1, value=m).border = self.border
            ws.cell(row=idx, column=2, value=v).border = self.border

    def _create_late_entry_sheet(self, wb, school_id, year, month, department=None):
        """Sheet for Late Entries (Arriving after grace period)"""
        ws = wb.create_sheet("Late Entries")
        ws['A1'] = f"Late Entry Report - {calendar.month_name[month]} {year}"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:G1')
        
        headers = ['Date', 'Staff ID', 'Name', 'Department', 'Shift Start', 'Punch In', 'Minutes Late']
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=h)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.border = self.border

        db = get_db()
        # Fetch all attendance records for the period and filter in Python for cross-platform stability
        records = db.execute('''
            SELECT ar.date as attendance_date, s.staff_id, s.full_name, s.department, 
                   sd.start_time, ar.time_in as punch_in, sd.grace_period_minutes
            FROM attendance ar
            JOIN staff s ON ar.staff_id = s.id
            JOIN shift_definitions sd ON ar.shift_type = sd.shift_type AND ar.school_id = sd.school_id
            WHERE ar.school_id = ? AND strftime('%Y', ar.date) = ? 
              AND strftime('%m', ar.date) = ?
              AND ar.time_in IS NOT NULL
        ''', (school_id, str(year), f"{month:02d}")).fetchall()

        row = 4
        for r in records:
            # Parse times safely
            try:
                # time_in might be just HH:MM:SS or full datetime
                punch_val = str(r['punch_in'])
                if ' ' in punch_val:
                    punch_in = datetime.strptime(punch_val, '%Y-%m-%d %H:%M:%S').time()
                else:
                    punch_in = datetime.strptime(punch_val, '%H:%M:%S').time()
                
                start_val = str(r['start_time'])
                start_time = datetime.strptime(start_val, '%H:%M:%S').time()
                
                # Convert to minutes from midnight for comparison
                punch_mins = punch_in.hour * 60 + punch_in.minute
                start_mins = start_time.hour * 60 + start_time.minute
                grace = int(r['grace_period_minutes'] or 0)
                
                if punch_mins > (start_mins + grace):
                    ws.cell(row=row, column=1, value=r['attendance_date']).border = self.border
                    ws.cell(row=row, column=2, value=r['staff_id']).border = self.border
                    ws.cell(row=row, column=3, value=r['full_name']).border = self.border
                    ws.cell(row=row, column=4, value=r['department']).border = self.border
                    ws.cell(row=row, column=5, value=r['start_time']).border = self.border
                    ws.cell(row=row, column=6, value=r['punch_in']).border = self.border
                    ws.cell(row=row, column=7, value=punch_mins - start_mins).border = self.border
                    row += 1
            except Exception:
                continue

    def _create_early_exit_sheet(self, wb, school_id, year, month, department=None):
        """Sheet for Early Exits (Leaving before shift end)"""
        ws = wb.create_sheet("Early Exits")
        ws['A1'] = f"Early Exit Report - {calendar.month_name[month]} {year}"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:G1')
        
        headers = ['Date', 'Staff ID', 'Name', 'Department', 'Shift End', 'Punch Out', 'Minutes Early']
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=h)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.border = self.border

        db = get_db()
        records = db.execute('''
            SELECT ar.date as attendance_date, s.staff_id, s.full_name, s.department, 
                   sd.end_time, ar.time_out as punch_out, sd.grace_period_minutes
            FROM attendance ar
            JOIN staff s ON ar.staff_id = s.id
            JOIN shift_definitions sd ON ar.shift_type = sd.shift_type AND ar.school_id = sd.school_id
            WHERE ar.school_id = ? AND strftime('%Y', ar.date) = ? 
              AND strftime('%m', ar.date) = ?
              AND ar.time_out IS NOT NULL AND ar.time_out != ''
        ''', (school_id, str(year), f"{month:02d}")).fetchall()

        row = 4
        for r in records:
            try:
                punch_val = str(r['punch_out'])
                if ' ' in punch_val:
                    punch_out = datetime.strptime(punch_val, '%Y-%m-%d %H:%M:%S').time()
                else:
                    punch_out = datetime.strptime(punch_val, '%H:%M:%S').time()
                
                end_val = str(r['end_time'])
                end_time = datetime.strptime(end_val, '%H:%M:%S').time()
                
                punch_mins = punch_out.hour * 60 + punch_out.minute
                end_mins = end_time.hour * 60 + end_time.minute
                grace = int(r['grace_period_minutes'] or 0)
                
                if punch_mins < (end_mins - grace):
                    ws.cell(row=row, column=1, value=r['attendance_date']).border = self.border
                    ws.cell(row=row, column=2, value=r['staff_id']).border = self.border
                    ws.cell(row=row, column=3, value=r['full_name']).border = self.border
                    ws.cell(row=row, column=4, value=r['department']).border = self.border
                    ws.cell(row=row, column=5, value=r['end_time']).border = self.border
                    ws.cell(row=row, column=6, value=r['punch_out']).border = self.border
                    ws.cell(row=row, column=7, value=end_mins - punch_mins).border = self.border
                    row += 1
            except Exception:
                continue

    def _create_shift_attendance_summary_sheet(self, wb, school_id, year, month, department=None):
        """Summary of attendance percentages per shift"""
        ws = wb.create_sheet("Shift Summary")
        ws['A1'] = f"Shift-Wise Attendance Summary - {calendar.month_name[month]} {year}"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:F1')
        
        headers = ['Shift Name', 'Total Staff Assigned', 'Total Present Days', 'Total Absent Days', 'Avg Presence %']
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=h)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.border = self.border

        db = get_db()
        shift_data = db.execute('''
            SELECT sd.shift_type, 
                   COUNT(DISTINCT s.id) as assigned_staff,
                   SUM(CASE WHEN ar.status = 'present' THEN 1 ELSE 0 END) as present_days,
                   SUM(CASE WHEN ar.status = 'absent' THEN 1 ELSE 0 END) as absent_days
            FROM shift_definitions sd
            LEFT JOIN staff s ON s.shift_type = sd.shift_type AND s.school_id = sd.school_id
            LEFT JOIN attendance ar ON ar.staff_id = s.id 
                 AND strftime('%Y', ar.date) = ? 
                 AND strftime('%m', ar.date) = ?
            WHERE sd.school_id = ?
            GROUP BY sd.shift_type
        ''', (str(year), f"{month:02d}", school_id)).fetchall()

        row = 4
        for d in shift_data:
            ws.cell(row=row, column=1, value=d['shift_type']).border = self.border
            ws.cell(row=row, column=2, value=d['assigned_staff']).border = self.border
            ws.cell(row=row, column=3, value=d['present_days']).border = self.border
            ws.cell(row=row, column=4, value=d['absent_days']).border = self.border
            
            total = d['present_days'] + d['absent_days']
            percent = (d['present_days'] / total * 100) if total > 0 else 0
            ws.cell(row=row, column=5, value=f"{percent:.2f}%").border = self.border
            row += 1

    def _create_absenteeism_analysis_sheet(self, wb, school_id, year, month, department=None):
        """Identify chronic absentees"""
        ws = wb.create_sheet("Absenteeism Analysis")
        ws['A1'] = f"Absenteeism Frequency Report - {calendar.month_name[month]} {year}"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:F1')
        
        headers = ['Staff ID', 'Name', 'Department', 'Total Absent Days', 'Absence %', 'Alert Status']
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=h)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.border = self.border

        db = get_db()
        # Days in month (approximate or precise)
        _, days_in_month = calendar.monthrange(year, month)
        
        absentee_data = db.execute('''
            SELECT s.staff_id, s.full_name, s.department, 
                   COUNT(ar.id) as absent_days
            FROM staff s
            JOIN attendance ar ON ar.staff_id = s.id
            WHERE ar.school_id = ? AND ar.status = 'absent'
              AND strftime('%Y', ar.date) = ? 
              AND strftime('%m', ar.date) = ?
            GROUP BY s.id
            HAVING absent_days > 2
            ORDER BY absent_days DESC
        ''', (school_id, str(year), f"{month:02d}")).fetchall()

        row = 4
        for d in absentee_data:
            ws.cell(row=row, column=1, value=d['staff_id']).border = self.border
            ws.cell(row=row, column=2, value=d['full_name']).border = self.border
            ws.cell(row=row, column=3, value=d['department']).border = self.border
            ws.cell(row=row, column=4, value=d['absent_days']).border = self.border
            
            absent_percent = (d['absent_days'] / days_in_month * 100)
            ws.cell(row=row, column=5, value=f"{absent_percent:.1f}%").border = self.border
            
            alert = "Critical" if absent_percent > 30 else ("High" if absent_percent > 15 else "Moderate")
            alert_cell = ws.cell(row=row, column=6, value=alert)
            alert_cell.border = self.border
            if alert == "Critical":
                alert_cell.fill = PatternFill(start_color="FFCCCC", end_color="FFCCCC", fill_type="solid")
            
            row += 1

    def _create_biometric_punch_log_sheet(self, wb, school_id, date, department=None):
        """Raw biometric logs for auditing"""
        ws = wb.create_sheet("Punch Logs")
        ws['A1'] = f"Detailed Biometric Punch Logs - {date}"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:F1')
        
        headers = ['Time', 'Staff ID', 'Name', 'Department', 'Device Name', 'Punch Type']
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=h)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.border = self.border

        db = get_db()
        # This assumes a raw_biometric_logs or similar table exists. 
        # If not, we fall back to attendance_records punch data.
        logs = db.execute('''
            SELECT ar.time_in as punch_time, s.staff_id, s.full_name, s.department, 'Device 1' as device, 'IN' as type
            FROM attendance ar
            JOIN staff s ON ar.staff_id = s.id
            WHERE ar.school_id = ? AND ar.date = ? AND ar.time_in IS NOT NULL
            UNION ALL
            SELECT ar.time_out as punch_time, s.staff_id, s.full_name, s.department, 'Device 1' as device, 'OUT' as type
            FROM attendance ar
            JOIN staff s ON ar.staff_id = s.id
            WHERE ar.school_id = ? AND ar.date = ? AND ar.time_out IS NOT NULL AND ar.time_out != ''
            ORDER BY punch_time ASC
        ''', (school_id, date, school_id, date)).fetchall()

        row = 4
        for l in logs:
            ws.cell(row=row, column=1, value=l['punch_time']).border = self.border
            ws.cell(row=row, column=2, value=l['staff_id']).border = self.border
            ws.cell(row=row, column=3, value=l['full_name']).border = self.border
            ws.cell(row=row, column=4, value=l['department']).border = self.border
            ws.cell(row=row, column=5, value=l['device']).border = self.border
            ws.cell(row=row, column=6, value=l['type']).border = self.border
            row += 1

    def _create_bank_advice_sheet(self, wb, school_id, year, month, department=None):
        """Bank Advice sheet with net pay and bank details"""
        ws = wb.create_sheet("Bank Advice")
        ws['A1'] = f"Bank Advice - Salary Disbursement - {calendar.month_name[month]} {year}"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:G1')
        
        headers = ['Sl No', 'Staff Name', 'Staff ID', 'Bank Name', 'Account Number', 'IFSC Code', 'Net Salary']
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=h)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.border = self.border

        # Get salary data using helper (history or on-the-fly)
        data = self._get_salary_data(school_id, year, month, department)

        row = 4
        total_net = 0
        for idx, r in enumerate(data, 1):
            ws.cell(row=row, column=1, value=idx).border = self.border
            ws.cell(row=row, column=2, value=r['full_name']).border = self.border
            ws.cell(row=row, column=3, value=r['staff_id']).border = self.border
            ws.cell(row=row, column=4, value=r['bank_name']).border = self.border
            ws.cell(row=row, column=5, value=r['bank_account_number']).border = self.border
            ws.cell(row=row, column=6, value=r['ifsc_code']).border = self.border
            ws.cell(row=row, column=7, value=r['net_salary']).border = self.border
            total_net += float(r['net_salary'] or 0)
            row += 1

        # Summary row
        ws.cell(row=row, column=6, value="Total Disbursement:").font = Font(bold=True)
        ws.cell(row=row, column=7, value=total_net).font = Font(bold=True)

    def _create_statutory_compliance_sheet(self, wb, school_id, year, month, department=None):
        """PF and ESI Compliance sheet"""
        ws = wb.create_sheet("PF & ESI Compliance")
        ws['A1'] = f"Statutory Compliance Report - {calendar.month_name[month]} {year}"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:I1')
        
        headers = ['Staff ID', 'Name', 'Gross Salary', 'PF Amount (Employee)', 'ESI Amount (Employee)', 'Total Deduction']
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=h)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.border = self.border
            
        # Get salary data using helper (history or on-the-fly)
        data = self._get_salary_data(school_id, year, month, department)
        # Filter for those with PF or ESI
        data = [r for r in data if float(r.get('assigned_pf') or r.get('pf_deduction') or 0) > 0 or 
                                 float(r.get('assigned_esi') or r.get('esi_deduction') or 0) > 0]

        row = 4
        for r in data:
            gross = float(r.get('gross_salary') or 0)
            # Use assigned values as requested
            pf_emp = float(r.get('assigned_pf') or r.get('pf_deduction') or 0)
            esi_emp = float(r.get('assigned_esi') or r.get('esi_deduction') or 0)
            
            ws.cell(row=row, column=1, value=r['staff_id']).border = self.border
            ws.cell(row=row, column=2, value=r['full_name']).border = self.border
            ws.cell(row=row, column=3, value=gross).border = self.border
            ws.cell(row=row, column=4, value=pf_emp).border = self.border
            ws.cell(row=row, column=5, value=esi_emp).border = self.border
            ws.cell(row=row, column=6, value=pf_emp + esi_emp).border = self.border
            row += 1

    def _create_deduction_analysis_sheet(self, wb, school_id, year, month, department=None):
        """Breakdown of all deductions"""
        ws = wb.create_sheet("Deduction Analysis")
        ws['A1'] = f"Monthly Deduction Analysis - {calendar.month_name[month]} {year}"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:G1')
        
        headers = ['Staff ID', 'Name', 'Absent Ded.', 'Late Penalty', 'Early Penalty', 'Single Punch', 'Manual Ded.', 'PF Ded.', 'ESI Ded.', 'PT', 'Other Ded.', 'Total']
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=h)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.border = self.border

        # Get salary data using helper (history or on-the-fly)
        data = self._get_salary_data(school_id, year, month, department)
        # Filter for those with deductions
        data = [r for r in data if float(r.get('total_deductions') or 0) > 0]

        row = 4
        for r in data:
            ws.cell(row=row, column=1, value=r['staff_id']).border = self.border
            ws.cell(row=row, column=2, value=r['full_name']).border = self.border
            ws.cell(row=row, column=3, value=r.get('absent_deduction', 0)).border = self.border
            ws.cell(row=row, column=4, value=r.get('late_penalty', 0)).border = self.border
            ws.cell(row=row, column=5, value=r.get('early_penalty', 0)).border = self.border
            ws.cell(row=row, column=6, value=r.get('single_punch_penalty', 0)).border = self.border
            ws.cell(row=row, column=7, value=r.get('manual_deduction', 0)).border = self.border
            ws.cell(row=row, column=8, value=r.get('pf_deduction', 0)).border = self.border
            ws.cell(row=row, column=9, value=r.get('esi_deduction', 0)).border = self.border
            ws.cell(row=row, column=10, value=r.get('professional_tax', 0)).border = self.border
            ws.cell(row=row, column=11, value=r.get('other_deductions', 0)).border = self.border
            ws.cell(row=row, column=12, value=r.get('total_deductions', 0)).border = self.border
            row += 1

    def _create_salary_structure_sheet(self, wb, school_id, department=None):
        """Staff CTC Structure sheet"""
        ws = wb.create_sheet("Salary Structure")
        ws['A1'] = f"Staff Salary Structure (CTC) - {datetime.now().strftime('%Y-%m-%d')}"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:H1')
        
        headers = ['Staff ID', 'Name', 'Department', 'Basic Salary', 'HRA', 'Allowance', 'Gross Monthly', 'Annual CTC']
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=h)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.border = self.border

        db = get_db()
        data = db.execute('''
            SELECT staff_id, full_name, department, basic_salary, hra, transport_allowance + other_allowances + dearness_allowance as total_allowance
            FROM staff
            WHERE school_id = ?
            ORDER BY department, full_name
        ''', (school_id,)).fetchall()

        row = 4
        for r in data:
            basic = float(r['basic_salary'] or 0)
            hra = float(r['hra'] or 0)
            allowance = float(r['total_allowance'] or 0)
            gross = basic + hra + allowance
            
            ws.cell(row=row, column=1, value=r['staff_id']).border = self.border
            ws.cell(row=row, column=2, value=r['full_name']).border = self.border
            ws.cell(row=row, column=3, value=r['department']).border = self.border
            ws.cell(row=row, column=4, value=basic).border = self.border
            ws.cell(row=row, column=5, value=hra).border = self.border
            ws.cell(row=row, column=6, value=allowance).border = self.border
            ws.cell(row=row, column=7, value=gross).border = self.border
            ws.cell(row=row, column=8, value=gross * 12).border = self.border
            row += 1

    def _create_audit_trail_sheet(self, wb, school_id, department=None):
        """Create a sheet showing chronological audit trail of admin actions"""
        ws = wb.create_sheet("Audit Trail")
        ws['A1'] = "Administrative Activity Audit Trail"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:G1')
        
        db = get_db()
        logs = db.execute('''
            SELECT a.username, al.action_type, al.action_details, 
                   al.ip_address, al.user_agent, al.created_at
            FROM admin_audit_logs al
            LEFT JOIN admins a ON al.admin_id = a.id
            WHERE al.school_id = ?
            ORDER BY al.created_at DESC
        ''', (school_id,)).fetchall()
        
        headers = ['Admin User', 'Action Type', 'Details', 'IP Address', 'User Agent', 'Timestamp']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.border = self.border

        row = 4
        for l in logs:
            ws.cell(row=row, column=1, value=l['username'] or "System").border = self.border
            ws.cell(row=row, column=2, value=l['action_type']).border = self.border
            ws.cell(row=row, column=3, value=l['action_details'] or "-").border = self.border
            ws.cell(row=row, column=4, value=l['ip_address']).border = self.border
            ws.cell(row=row, column=5, value=l['user_agent'][:50] + "..." if l['user_agent'] else "-").border = self.border
            ws.cell(row=row, column=6, value=l['created_at']).border = self.border
            
            # Color code report generation differently
            if l['action_type'] == 'Report Generation':
                ws.cell(row=row, column=2).fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
            
            row += 1

    def _save_workbook_to_response(self, wb, filename):
        """Save workbook to a Flask response object"""
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response

    def _create_staff_profile_sheet(self, wb, school_id):
        """Create staff profile sheet"""
        ws = wb.create_sheet("Staff Profiles")
        if self.generated_by:
            ws['A2'] = f"Generated by: {self.generated_by}"

        # Title
        ws['A1'] = "Staff Profiles"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:G1')

        # Headers
        headers = ['Staff ID', 'Full Name', 'Department', 'Position', 'Email', 'Phone', 'Join Date']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = Alignment(horizontal='center')

        # Get data
        db = get_db()
        query = '''
            SELECT staff_id, full_name, department, destination, email, phone, created_at
            FROM staff
            WHERE school_id = ?
            ORDER BY full_name
        '''
        sql_params = [school_id]
        if department:
            query = query.replace('WHERE school_id = ?', 'WHERE school_id = ? AND department = ?')
            sql_params.append(department)
        staff_data = db.execute(query, sql_params).fetchall()

        # Add data
        for row, staff in enumerate(staff_data, 4):
            ws.cell(row=row, column=1, value=staff['staff_id'])
            ws.cell(row=row, column=2, value=staff['full_name'])
            ws.cell(row=row, column=3, value=staff['department'] or 'N/A')
            ws.cell(row=row, column=4, value=staff['destination'] or 'N/A')
            ws.cell(row=row, column=5, value=staff['email'] or 'N/A')
            ws.cell(row=row, column=6, value=staff['phone'] or 'N/A')
            ws.cell(row=row, column=7, value=staff['created_at'][:10] if staff['created_at'] else 'N/A')

        # Format columns
        column_widths = [12, 20, 15, 15, 25, 15, 12]
        for col, width in enumerate(column_widths, 1):
            ws.column_dimensions[chr(64 + col)].width = width

        # Add borders
        for row in range(3, len(staff_data) + 4):
            for col in range(1, 8):
                ws.cell(row=row, column=col).border = self.border

    def _create_department_analysis_sheet(self, wb, school_id, start_date, end_date):
        """Create department-wise analysis sheet"""
        ws = wb.create_sheet("Department Analysis")

        # Title
        ws['A1'] = "Department-wise Attendance Analysis"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:F1')

        # Headers
        headers = ['Department', 'Total Staff', 'Present Days', 'Absent Days', 'Attendance Rate', 'Late Arrivals']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = Alignment(horizontal='center')

        # Get data
        db = get_db()
        dept_data = db.execute('''
            SELECT
                COALESCE(s.department, 'Unassigned') as department,
                COUNT(DISTINCT s.id) as total_staff,
                COUNT(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1 END) as present_days,
                COUNT(CASE WHEN a.status = 'absent' THEN 1 END) as absent_days,
                COUNT(CASE WHEN a.status = 'late' THEN 1 END) as late_arrivals
            FROM staff s
            LEFT JOIN attendance a ON s.id = a.staff_id AND a.date BETWEEN ? AND ?
            WHERE s.school_id = ?
            GROUP BY s.department
            ORDER BY department
        ''', (start_date, end_date, school_id)).fetchall()

        # Add data
        for row, dept in enumerate(dept_data, 4):
            total_records = dept['present_days'] + dept['absent_days']
            attendance_rate = (dept['present_days'] / total_records * 100) if total_records > 0 else 0

            ws.cell(row=row, column=1, value=dept['department'])
            ws.cell(row=row, column=2, value=dept['total_staff'])
            ws.cell(row=row, column=3, value=dept['present_days'])
            ws.cell(row=row, column=4, value=dept['absent_days'])
            ws.cell(row=row, column=5, value=f"{attendance_rate:.1f}%")
            ws.cell(row=row, column=6, value=dept['late_arrivals'])

        # Format columns
        column_widths = [15, 12, 12, 12, 15, 12]
        for col, width in enumerate(column_widths, 1):
            ws.column_dimensions[chr(64 + col)].width = width

        # Add borders
        for row in range(3, len(dept_data) + 4):
            for col in range(1, 7):
                ws.cell(row=row, column=col).border = self.border

    def _create_charts_sheet(self, wb, school_id, start_date, end_date):
        """Create charts and visualizations sheet"""
        ws = wb.create_sheet("Charts & Analytics")

        # Title
        ws['A1'] = "Attendance Analytics & Charts"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:H1')

        # Create attendance status pie chart
        db = get_db()
        status_data = db.execute('''
            SELECT status, COUNT(*) as count
            FROM attendance
            WHERE school_id = ? AND date BETWEEN ? AND ?
            GROUP BY status
        ''', (school_id, start_date, end_date)).fetchall()

        # Add data for pie chart
        ws['A3'] = "Attendance Status Distribution"
        ws['A3'].font = Font(bold=True, size=12)

        ws['A4'] = "Status"
        ws['B4'] = "Count"
        for col in [1, 2]:
            cell = ws.cell(row=4, column=col)
            cell.font = self.header_font
            cell.fill = self.header_fill

        for row, status in enumerate(status_data, 5):
            ws.cell(row=row, column=1, value=status['status'].title())
            ws.cell(row=row, column=2, value=status['count'])

        # Create pie chart
        pie_chart = PieChart()
        labels = Reference(ws, min_col=1, min_row=5, max_row=4 + len(status_data))
        data = Reference(ws, min_col=2, min_row=4, max_row=4 + len(status_data))
        pie_chart.add_data(data, titles_from_data=True)
        pie_chart.set_categories(labels)
        pie_chart.title = "Attendance Status Distribution"
        ws.add_chart(pie_chart, "D3")

        # Daily attendance trend
        daily_data = db.execute('''
            SELECT date,
                   COUNT(CASE WHEN status IN ('present', 'late', 'on_duty') THEN 1 END) as present_count,
                   COUNT(CASE WHEN status = 'absent' THEN 1 END) as absent_count
            FROM attendance
            WHERE school_id = ? AND date BETWEEN ? AND ?
            GROUP BY date
            ORDER BY date
        ''', (school_id, start_date, end_date)).fetchall()

        # Add daily trend data
        ws['A15'] = "Daily Attendance Trend"
        ws['A15'].font = Font(bold=True, size=12)

        headers = ['Date', 'Present', 'Absent']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=16, column=col)
            cell.value = header
            cell.font = self.header_font
            cell.fill = self.header_fill

        for row, day in enumerate(daily_data, 17):
            ws.cell(row=row, column=1, value=day['date'])
            ws.cell(row=row, column=2, value=day['present_count'])
            ws.cell(row=row, column=3, value=day['absent_count'])

        # Create line chart for daily trend
        line_chart = LineChart()
        line_chart.title = "Daily Attendance Trend"
        line_chart.y_axis.title = "Number of Staff"
        line_chart.x_axis.title = "Date"

        data = Reference(ws, min_col=2, min_row=16, max_col=3, max_row=16 + len(daily_data))
        categories = Reference(ws, min_col=1, min_row=17, max_row=16 + len(daily_data))
        line_chart.add_data(data, titles_from_data=True)
        line_chart.set_categories(categories)
        ws.add_chart(line_chart, "D15")

    def _create_individual_summary_sheet(self, wb, staff_id, start_date, end_date):
        """Create individual staff summary sheet"""
        ws = wb.create_sheet("Personal Summary")

        db = get_db()
        staff = db.execute('SELECT * FROM staff WHERE id = ?', (staff_id,)).fetchone()

        # Title
        ws['A1'] = f"Personal Attendance Report - {staff['full_name']}"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:D1')
        if self.generated_by:
            ws['A2'] = f"Generated by: {self.generated_by}"

        # Staff details
        ws['A3'] = "Staff Information"
        ws['A3'].font = Font(bold=True, size=12)

        staff_info = [
            ('Staff ID:', staff['staff_id']),
            ('Full Name:', staff['full_name']),
            ('Department:', staff['department'] or 'N/A'),
            ('Position:', staff['destination'] or 'N/A'),
            ('Email:', staff['email'] or 'N/A'),
            ('Phone:', staff['phone'] or 'N/A')
        ]

        for row, (label, value) in enumerate(staff_info, 4):
            ws.cell(row=row, column=1, value=label).font = Font(bold=True)
            ws.cell(row=row, column=2, value=value)

        # Attendance summary
        ws['A11'] = "Attendance Summary"
        ws['A11'].font = Font(bold=True, size=12)

        # Calculate attendance metrics
        attendance_data = db.execute('''
            SELECT status, COUNT(*) as count
            FROM attendance
            WHERE staff_id = ? AND date BETWEEN ? AND ?
            GROUP BY status
        ''', (staff_id, start_date, end_date)).fetchall()

        total_days = sum(record['count'] for record in attendance_data)
        present_days = sum(record['count'] for record in attendance_data if record['status'] in ['present', 'late', 'on_duty'])

        summary_data = [
            ('Total Working Days:', total_days),
            ('Present Days:', present_days),
            ('Attendance Rate:', f"{(present_days/total_days*100):.1f}%" if total_days > 0 else "0%")
        ]

        for row, (label, value) in enumerate(summary_data, 12):
            ws.cell(row=row, column=1, value=label).font = Font(bold=True)
            ws.cell(row=row, column=2, value=value)

        # Format columns
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 20

    def _create_individual_detailed_sheet(self, wb, staff_id, start_date, end_date):
        """Create individual detailed attendance sheet"""
        ws = wb.create_sheet("Detailed Records")

        # Title
        ws['A1'] = "Detailed Attendance Records"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:F1')

        # Headers
        headers = ['Date', 'Time In', 'Time Out', 'Status', 'Hours Worked', 'Notes']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = Alignment(horizontal='center')

        # Get data
        db = get_db()
        attendance_records = db.execute('''
            SELECT date, time_in, time_out, status, notes
            FROM attendance
            WHERE staff_id = ? AND date BETWEEN ? AND ?
            ORDER BY date DESC
        ''', (staff_id, start_date, end_date)).fetchall()

        # Add data
        for row, record in enumerate(attendance_records, 4):
            ws.cell(row=row, column=1, value=record['date'])
            ws.cell(row=row, column=2, value=record['time_in'])
            ws.cell(row=row, column=3, value=record['time_out'])
            ws.cell(row=row, column=4, value=record['status'].title())

            # Calculate hours worked
            if record['time_in'] and record['time_out']:
                try:
                    time_in = datetime.strptime(record['time_in'], '%H:%M:%S').time()
                    time_out = datetime.strptime(record['time_out'], '%H:%M:%S').time()
                    time_in_dt = datetime.combine(datetime.today(), time_in)
                    time_out_dt = datetime.combine(datetime.today(), time_out)
                    if time_out_dt < time_in_dt:  # Next day checkout
                        time_out_dt += timedelta(days=1)
                    hours_worked = (time_out_dt - time_in_dt).total_seconds() / 3600
                    ws.cell(row=row, column=5, value=f"{hours_worked:.1f}h")
                except:
                    ws.cell(row=row, column=5, value="N/A")
            else:
                ws.cell(row=row, column=5, value="N/A")

            ws.cell(row=row, column=6, value=record['notes'] or '')

        # Format columns
        column_widths = [12, 10, 10, 12, 12, 30]
        for col, width in enumerate(column_widths, 1):
            ws.column_dimensions[chr(64 + col)].width = width

        # Add borders
        for row in range(3, len(attendance_records) + 4):
            for col in range(1, 7):
                ws.cell(row=row, column=col).border = self.border

    def _create_individual_charts_sheet(self, wb, staff_id, start_date, end_date):
        """Create individual charts sheet"""
        ws = wb.create_sheet("Personal Analytics")

        # Title
        ws['A1'] = "Personal Attendance Analytics"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:F1')

        # Monthly attendance trend
        db = get_db()
        monthly_data = db.execute('''
            SELECT strftime('%Y-%m', date) as month,
                   COUNT(CASE WHEN status IN ('present', 'late', 'on_duty') THEN 1 END) as present_days,
                   COUNT(*) as total_days
            FROM attendance
            WHERE staff_id = ? AND date BETWEEN ? AND ?
            GROUP BY strftime('%Y-%m', date)
            ORDER BY month
        ''', (staff_id, start_date, end_date)).fetchall()

        # Add monthly trend data
        ws['A3'] = "Monthly Attendance Trend"
        ws['A3'].font = Font(bold=True, size=12)

        headers = ['Month', 'Present Days', 'Total Days', 'Attendance %']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col)
            cell.value = header
            cell.font = self.header_font
            cell.fill = self.header_fill

        for row, month in enumerate(monthly_data, 5):
            attendance_pct = (month['present_days'] / month['total_days'] * 100) if month['total_days'] > 0 else 0
            ws.cell(row=row, column=1, value=month['month'])
            ws.cell(row=row, column=2, value=month['present_days'])
            ws.cell(row=row, column=3, value=month['total_days'])
            ws.cell(row=row, column=4, value=f"{attendance_pct:.1f}%")

        # Format columns
        for col in range(1, 5):
            ws.column_dimensions[chr(64 + col)].width = 15

    def _create_company_summary_sheet(self, wb, start_date, end_date):
        """Create company-wide summary sheet"""
        ws = wb.create_sheet("Company Summary")

        # Title
        ws['A1'] = "Company-wide Attendance Summary"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:F1')

        ws['A3'] = f"Report Period: {start_date} to {end_date}"
        ws['A4'] = f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        if self.generated_by:
            ws['A5'] = f"Generated by: {self.generated_by}"

        # Headers
        headers = ['School Name', 'Total Staff', 'Total Records', 'Present Days', 'Attendance Rate', 'Late Arrivals']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=6, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = Alignment(horizontal='center')

        # Get data
        db = get_db()
        school_data = db.execute('''
            SELECT
                s.name as school_name,
                COUNT(DISTINCT st.id) as total_staff,
                COUNT(a.id) as total_records,
                COUNT(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1 END) as present_days,
                COUNT(CASE WHEN a.status = 'late' THEN 1 END) as late_arrivals
            FROM schools s
            LEFT JOIN staff st ON s.id = st.school_id
            LEFT JOIN attendance a ON st.id = a.staff_id AND a.date BETWEEN ? AND ?
            GROUP BY s.id, s.name
            ORDER BY s.name
        ''', (start_date, end_date)).fetchall()

        # Add data
        for row, school in enumerate(school_data, 7):
            attendance_rate = (school['present_days'] / school['total_records'] * 100) if school['total_records'] > 0 else 0

            ws.cell(row=row, column=1, value=school['school_name'])
            ws.cell(row=row, column=2, value=school['total_staff'])
            ws.cell(row=row, column=3, value=school['total_records'])
            ws.cell(row=row, column=4, value=school['present_days'])
            ws.cell(row=row, column=5, value=f"{attendance_rate:.1f}%")
            ws.cell(row=row, column=6, value=school['late_arrivals'])

        # Format columns
        column_widths = [25, 12, 15, 12, 15, 12]
        for col, width in enumerate(column_widths, 1):
            ws.column_dimensions[chr(64 + col)].width = width

        # Add borders
        for row in range(6, len(school_data) + 7):
            for col in range(1, 7):
                ws.cell(row=row, column=col).border = self.border

    def _create_school_comparison_sheet(self, wb, start_date, end_date):
        """Create school comparison sheet"""
        ws = wb.create_sheet("School Comparison")

        # Title
        ws['A1'] = "School Performance Comparison"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:E1')

        # Get comparative data
        db = get_db()
        comparison_data = db.execute('''
            SELECT
                s.name as school_name,
                COUNT(DISTINCT st.id) as total_staff,
                ROUND(AVG(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1.0 ELSE 0.0 END) * 100, 2) as avg_attendance_rate,
                COUNT(CASE WHEN a.status = 'late' THEN 1 END) as total_late_arrivals,
                COUNT(CASE WHEN a.status = 'absent' THEN 1 END) as total_absences
            FROM schools s
            LEFT JOIN staff st ON s.id = st.school_id
            LEFT JOIN attendance a ON st.id = a.staff_id AND a.date BETWEEN ? AND ?
            GROUP BY s.id, s.name
            ORDER BY avg_attendance_rate DESC
        ''', (start_date, end_date)).fetchall()

        # Headers
        headers = ['Rank', 'School Name', 'Staff Count', 'Attendance Rate', 'Performance']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = Alignment(horizontal='center')

        # Add ranked data
        for row, (rank, school) in enumerate(enumerate(comparison_data, 1), 4):
            performance = "Excellent" if school['avg_attendance_rate'] >= 95 else \
                         "Good" if school['avg_attendance_rate'] >= 85 else \
                         "Average" if school['avg_attendance_rate'] >= 75 else "Needs Improvement"

            ws.cell(row=row, column=1, value=rank)
            ws.cell(row=row, column=2, value=school['school_name'])
            ws.cell(row=row, column=3, value=school['total_staff'])
            ws.cell(row=row, column=4, value=f"{school['avg_attendance_rate']:.1f}%")
            ws.cell(row=row, column=5, value=performance)

        # Format columns
        column_widths = [8, 25, 12, 15, 18]
        for col, width in enumerate(column_widths, 1):
            ws.column_dimensions[chr(64 + col)].width = width

    def _create_company_charts_sheet(self, wb, start_date, end_date):
        """Create company charts sheet"""
        ws = wb.create_sheet("Company Analytics")

        # Title
        ws['A1'] = "Company-wide Analytics"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:F1')

        # School performance comparison chart data
        db = get_db()
        chart_data = db.execute('''
            SELECT
                s.name as school_name,
                ROUND(AVG(CASE WHEN a.status IN ('present', 'late', 'on_duty') THEN 1.0 ELSE 0.0 END) * 100, 1) as attendance_rate
            FROM schools s
            LEFT JOIN staff st ON s.id = st.school_id
            LEFT JOIN attendance a ON st.id = a.staff_id AND a.date BETWEEN ? AND ?
            GROUP BY s.id, s.name
            ORDER BY attendance_rate DESC
        ''', (start_date, end_date)).fetchall()

        # Add chart data
        ws['A3'] = "School Performance Comparison"
        ws['A3'].font = Font(bold=True, size=12)

        headers = ['School', 'Attendance Rate (%)']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col)
            cell.value = header
            cell.font = self.header_font
            cell.fill = self.header_fill

        for row, school in enumerate(chart_data, 5):
            ws.cell(row=row, column=1, value=school['school_name'])
            ws.cell(row=row, column=2, value=school['attendance_rate'])

        # Create bar chart
        bar_chart = BarChart()
        bar_chart.title = "School Attendance Rate Comparison"
        bar_chart.y_axis.title = "Attendance Rate (%)"
        bar_chart.x_axis.title = "Schools"

        data = Reference(ws, min_col=2, min_row=4, max_row=4 + len(chart_data))
        categories = Reference(ws, min_col=1, min_row=5, max_row=4 + len(chart_data))
        bar_chart.add_data(data, titles_from_data=True)
        bar_chart.set_categories(categories)
        ws.add_chart(bar_chart, "D3")

    def _create_monthly_staff_records_sheet(self, wb, school_id, year, month, department=None):
        """Create individual staff records sheet for monthly attendance"""
        ws = wb.create_sheet("Staff Records")
        
        # Title
        ws['A1'] = f"Monthly Staff Attendance Records - {year}/{month:02d}"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:I1')
        
        # Date range info
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
        
        ws['A2'] = f"Period: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}"
        ws['A2'].font = Font(bold=True, size=11)
        
        db = get_db()
        school = db.execute('SELECT name FROM schools WHERE id = ?', (school_id,)).fetchone()
        ws['A3'] = f"School: {school['name'] if school else 'Unknown'}"
        if self.generated_by:
            ws['A4'] = f"Generated by: {self.generated_by}"
        
        # Headers
        headers = [
            'Staff ID', 'Staff Name', 'Department', 'Position',
            'Total Working Days', 'Absent (count)', 'Leave (count)',
            'On Duty (OD) (count)', 'Total Present Days'
        ]
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=5, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = Alignment(horizontal='center')
            cell.border = self.border
        
        # Calculate total working days in the month (business days)
        import calendar
        total_days_in_month = (end_date - start_date).days + 1
        
        # Count business days (excluding only Sundays) for more accurate working days
        business_days_count = 0
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() < 6:  # Monday-Saturday = 0-5, Sunday = 6
                business_days_count += 1
            current_date += timedelta(days=1)
        
        # Get individual staff monthly attendance summary with corrected calculations
        staff_records = db.execute('''
            SELECT 
                s.staff_id,
                s.full_name,
                s.department,
                COALESCE(s.destination, '') as position,
                COUNT(CASE WHEN a.status = 'absent' THEN 1 END) as recorded_absent_count,
                COUNT(CASE WHEN a.status = 'leave' THEN 1 END) as leave_count,
                COUNT(CASE WHEN a.status = 'on_duty' THEN 1 END) as on_duty_count,
                COUNT(CASE WHEN a.status IN ('present', 'late', 'early_departure') THEN 1 END) as recorded_present_count,
                COUNT(CASE WHEN a.date IS NOT NULL THEN 1 END) as total_recorded_days
            FROM staff s
            LEFT JOIN attendance a ON s.id = a.staff_id 
                AND a.date BETWEEN ? AND ?
                AND a.school_id = ?
            WHERE s.school_id = ? AND s.is_active = 1
            GROUP BY s.id, s.staff_id, s.full_name, s.department, s.destination
            ORDER BY CAST(s.staff_id AS INTEGER) ASC
        ''', (start_date, end_date, school_id, school_id)).fetchall()
        
        # Store corrected values for totals calculation
        corrected_staff_data = []
        
        # Add staff data with corrected calculations
        row = 6
        for staff in staff_records:
            # Calculate corrected values
            working_days = business_days_count
            leave_count = staff['leave_count']
            on_duty_count = staff['on_duty_count']
            recorded_present = staff['recorded_present_count']
            
            # Present count includes actual present + late + on_duty days
            total_present_days = recorded_present + on_duty_count
            
            # Absent count = Working days - (Present + Leave + On Duty)
            # But we need to account for days without attendance records
            recorded_days = staff['total_recorded_days']
            unrecorded_days = working_days - recorded_days
            
            # If there are unrecorded days, we assume they are absent
            actual_absent_count = staff['recorded_absent_count'] + unrecorded_days
            
            # Store corrected data for totals
            corrected_data = {
                'working_days': working_days,
                'absent_count': actual_absent_count,
                'leave_count': leave_count,
                'on_duty_count': on_duty_count,
                'present_count': total_present_days
            }
            corrected_staff_data.append(corrected_data)
            
            values = [
                staff['staff_id'],
                staff['full_name'],
                staff['department'] or 'Unassigned',
                staff['position'],
                working_days,  # Total working days (business days)
                actual_absent_count,  # Corrected absent count
                leave_count,
                on_duty_count,
                total_present_days  # Corrected present count
            ]
            
            for col, value in enumerate(values, 1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.border = self.border
                
                # Add conditional formatting for better readability
                if col == 6 and value > 5:  # High absence count
                    cell.fill = PatternFill(start_color='FFCCCC', end_color='FFCCCC', fill_type='solid')
                elif col == 9 and working_days > 0:  # Attendance rate coloring based on present days
                    rate = value / working_days
                    if rate >= 0.95:  # Excellent attendance
                        cell.fill = PatternFill(start_color='CCFFCC', end_color='CCFFCC', fill_type='solid')
                    elif rate < 0.80:  # Poor attendance
                        cell.fill = PatternFill(start_color='FFCCCC', end_color='FFCCCC', fill_type='solid')
            
            row += 1
        
        # Add summary row
        if corrected_staff_data:
            row += 1
            
            # Calculate totals using corrected data
            total_staff = len(corrected_staff_data)
            total_working_days_display = total_staff * business_days_count
            total_absent = sum(record['absent_count'] for record in corrected_staff_data)
            total_leave = sum(record['leave_count'] for record in corrected_staff_data)
            total_on_duty = sum(record['on_duty_count'] for record in corrected_staff_data)
            total_present = sum(record['present_count'] for record in corrected_staff_data)
            
            # Create summary row values with proper structure
            summary_values = [
                "TOTALS:",
                f"{total_staff} Staff",
                "",
                "",
                total_working_days_display,
                total_absent,
                total_leave,
                total_on_duty,
                total_present
            ]
            
            for col, value in enumerate(summary_values, 1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.font = Font(bold=True)
                cell.border = self.border
                if col == 1:  # "TOTALS:" label
                    cell.fill = PatternFill(start_color='D3D3D3', end_color='D3D3D3', fill_type='solid')
                else:  # Data cells
                    cell.fill = PatternFill(start_color='E6E6FA', end_color='E6E6FA', fill_type='solid')
        
        # Format columns
        column_widths = [12, 25, 18, 18, 16, 14, 12, 16, 16]
        for col, width in enumerate(column_widths, 1):
            ws.column_dimensions[chr(64 + col)].width = width
        
        # Add notes
        notes_row = row + 3
        ws.cell(row=notes_row, column=1, value="Notes:").font = Font(bold=True)
        ws.cell(row=notes_row + 1, column=1, value=f"• Total Working Days: {business_days_count} business days in {year}/{month:02d}")
        ws.cell(row=notes_row + 2, column=1, value="• Staff ID sorted in ascending numerical order") 
        ws.cell(row=notes_row + 3, column=1, value="• Absent count = Working days - (Present + Leave + On Duty)")
        ws.cell(row=notes_row + 4, column=1, value="• Total Present Days = Present + Late + On Duty")
        ws.cell(row=notes_row + 5, column=1, value="• Days without attendance records are counted as absent")
        ws.cell(row=notes_row + 6, column=1, value="• Green highlighting = Excellent attendance (≥95%)")
        ws.cell(row=notes_row + 7, column=1, value="• Red highlighting = High absence count (>5) or poor attendance (<80%)")

    def _create_monthly_summary_sheet(self, wb, school_id, year, month, department=None):
        """Create monthly summary sheet"""
        ws = wb.create_sheet("Monthly Summary")

        # Title
        ws['A1'] = f"Monthly Attendance Report - {year}/{month:02d}"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:F1')

        db = get_db()
        school = db.execute('SELECT name FROM schools WHERE id = ?', (school_id,)).fetchone()
        ws['A3'] = f"School: {school['name'] if school else 'Unknown'}"

        # Monthly statistics
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)

        # Get monthly stats
        monthly_stats = db.execute('''
            SELECT
                COUNT(DISTINCT staff_id) as active_staff,
                COUNT(*) as total_records,
                COUNT(CASE WHEN status IN ('present', 'late', 'on_duty') THEN 1 END) as present_days,
                COUNT(CASE WHEN status = 'absent' THEN 1 END) as absent_days,
                COUNT(CASE WHEN status = 'late' THEN 1 END) as late_days,
                COUNT(CASE WHEN status = 'leave' THEN 1 END) as leave_days
            FROM attendance
            WHERE school_id = ? AND date BETWEEN ? AND ?
        ''', (school_id, start_date, end_date)).fetchone()

        # Display stats
        ws['A5'] = "Monthly Statistics"
        ws['A5'].font = Font(bold=True, size=12)

        stats = [
            ('Active Staff:', monthly_stats['active_staff']),
            ('Total Records:', monthly_stats['total_records']),
            ('Present Days:', monthly_stats['present_days']),
            ('Absent Days:', monthly_stats['absent_days']),
            ('Late Arrivals:', monthly_stats['late_days']),
            ('Leave Days:', monthly_stats['leave_days']),
            ('Attendance Rate:', f"{(monthly_stats['present_days']/monthly_stats['total_records']*100):.1f}%" if monthly_stats['total_records'] > 0 else "0%")
        ]

        for row, (label, value) in enumerate(stats, 6):
            ws.cell(row=row, column=1, value=label).font = Font(bold=True)
            ws.cell(row=row, column=2, value=value)

        # Format columns
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 15

    def _create_monthly_calendar_sheet(self, wb, school_id, year, month):
        """Create monthly calendar view sheet"""
        ws = wb.create_sheet("Monthly Calendar")

        # Title
        ws['A1'] = f"Monthly Calendar View - {year}/{month:02d}"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:H1')

        # Calendar headers
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for col, day in enumerate(days, 1):
            cell = ws.cell(row=3, column=col, value=day)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = Alignment(horizontal='center')

        # Get daily attendance summary for the month
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)

        db = get_db()
        daily_summary = db.execute('''
            SELECT date,
                   COUNT(CASE WHEN status IN ('present', 'late', 'on_duty') THEN 1 END) as present_count,
                   COUNT(CASE WHEN status = 'absent' THEN 1 END) as absent_count,
                   COUNT(*) as total_count
            FROM attendance
            WHERE school_id = ? AND date BETWEEN ? AND ?
            GROUP BY date
            ORDER BY date
        ''', (school_id, start_date, end_date)).fetchall()

        # Create calendar grid
        current_date = start_date
        row = 4
        col = current_date.weekday() + 1  # Monday = 0, so add 1 for column

        daily_data = {record['date']: record for record in daily_summary}

        while current_date <= end_date:
            if col > 7:
                col = 1
                row += 3  # Leave space for attendance data

            # Date
            ws.cell(row=row, column=col, value=current_date.day).font = Font(bold=True)

            # Attendance data
            if current_date.strftime('%Y-%m-%d') in daily_data:
                data = daily_data[current_date.strftime('%Y-%m-%d')]
                ws.cell(row=row+1, column=col, value=f"P: {data['present_count']}")
                ws.cell(row=row+2, column=col, value=f"A: {data['absent_count']}")

            current_date += timedelta(days=1)
            col += 1

        # Format columns
        for col in range(1, 8):
            ws.column_dimensions[chr(64 + col)].width = 12

    def _create_monthly_trends_sheet(self, wb, school_id, year, month):
        """Create monthly trends analysis sheet"""
        ws = wb.create_sheet("Monthly Trends")

        # Title
        ws['A1'] = f"Monthly Trends Analysis - {year}/{month:02d}"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:F1')

        # Weekly breakdown
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)

        db = get_db()
        weekly_data = db.execute('''
            SELECT
                strftime('%W', date) as week_number,
                COUNT(CASE WHEN status IN ('present', 'late', 'on_duty') THEN 1 END) as present_count,
                COUNT(CASE WHEN status = 'absent' THEN 1 END) as absent_count,
                COUNT(*) as total_count
            FROM attendance
            WHERE school_id = ? AND date BETWEEN ? AND ?
            GROUP BY strftime('%W', date)
            ORDER BY week_number
        ''', (school_id, start_date, end_date)).fetchall()

        # Add weekly data
        ws['A3'] = "Weekly Breakdown"
        ws['A3'].font = Font(bold=True, size=12)

        headers = ['Week', 'Present', 'Absent', 'Total', 'Attendance %']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col)
            cell.value = header
            cell.font = self.header_font
            cell.fill = self.header_fill

        for row, week in enumerate(weekly_data, 5):
            attendance_pct = (week['present_count'] / week['total_count'] * 100) if week['total_count'] > 0 else 0
            ws.cell(row=row, column=1, value=f"Week {week['week_number']}")
            ws.cell(row=row, column=2, value=week['present_count'])
            ws.cell(row=row, column=3, value=week['absent_count'])
            ws.cell(row=row, column=4, value=week['total_count'])
            ws.cell(row=row, column=5, value=f"{attendance_pct:.1f}%")

        # Format columns
        for col in range(1, 6):
            ws.column_dimensions[chr(64 + col)].width = 12

    def _create_overtime_records_sheet(self, wb, school_id, year, month, department=None):
        """Create individual staff overtime records sheet"""
        ws = wb.create_sheet("Overtime Records")
        
        # Title
        ws['A1'] = f"Staff Overtime Records - {year}/{month:02d}"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:G1')
        if self.generated_by:
            ws['A2'] = f"Generated by: {self.generated_by}"
        
        # Date range info
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
        
        ws['A2'] = f"Period: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}"
        ws['A2'].font = Font(bold=True, size=11)
        
        db = get_db()
        school = db.execute('SELECT name FROM schools WHERE id = ?', (school_id,)).fetchone()
        ws['A3'] = f"School: {school['name'] if school else 'Unknown'}"
        
        # Headers
        headers = [
            'Staff ID', 'Staff Name', 'Department', 'Position',
            'Total Overtime Days', 'Total Overtime Hours', 'Overtime Details'
        ]
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=5, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = Alignment(horizontal='center')
            cell.border = self.border
        
        # Helper function to calculate overtime hours
        def calculate_overtime_hours(overtime_in, overtime_out):
            if not overtime_in or not overtime_out:
                return 0.0
            try:
                # Convert time strings to datetime objects for calculation
                if isinstance(overtime_in, str):
                    in_time = datetime.strptime(overtime_in, '%H:%M:%S').time()
                else:
                    in_time = overtime_in
                
                if isinstance(overtime_out, str):
                    out_time = datetime.strptime(overtime_out, '%H:%M:%S').time()
                else:
                    out_time = overtime_out
                
                # Calculate duration in hours
                in_minutes = in_time.hour * 60 + in_time.minute
                out_minutes = out_time.hour * 60 + out_time.minute
                
                # Handle overnight overtime
                if out_minutes < in_minutes:
                    out_minutes += 24 * 60
                
                duration_minutes = out_minutes - in_minutes
                return round(duration_minutes / 60.0, 2)
            except:
                return 0.0
        
        # Get individual staff overtime data with detailed breakdown
        staff_overtime_data = db.execute('''
            SELECT 
                s.staff_id,
                s.full_name,
                s.department,
                COALESCE(s.destination, '') as position,
                COUNT(CASE WHEN a.overtime_in IS NOT NULL AND a.overtime_out IS NOT NULL THEN 1 END) as overtime_days,
                GROUP_CONCAT(
                    CASE 
                        WHEN a.overtime_in IS NOT NULL AND a.overtime_out IS NOT NULL 
                        THEN a.date || ' (' || a.overtime_in || '-' || a.overtime_out || ')'
                    END, 
                    '; '
                ) as overtime_details,
                a.overtime_in,
                a.overtime_out
            FROM staff s
            LEFT JOIN attendance a ON s.id = a.staff_id 
                AND a.date BETWEEN ? AND ?
                AND a.school_id = ?
                AND (a.overtime_in IS NOT NULL OR a.overtime_out IS NOT NULL)
            WHERE s.school_id = ? AND s.is_active = 1
            GROUP BY s.id, s.staff_id, s.full_name, s.department, s.destination
            ORDER BY CAST(s.staff_id AS INTEGER) ASC
        ''', (start_date, end_date, school_id, school_id)).fetchall()
        
        # Calculate total hours for each staff member and collect data for totals
        corrected_staff_data = []
        row = 6
        
        for staff in staff_overtime_data:
            # Get detailed overtime records for this staff member
            overtime_records = db.execute('''
                SELECT overtime_in, overtime_out, date
                FROM attendance a
                JOIN staff s ON s.id = a.staff_id
                WHERE s.staff_id = ? AND s.school_id = ?
                    AND a.date BETWEEN ? AND ?
                    AND a.overtime_in IS NOT NULL 
                    AND a.overtime_out IS NOT NULL
            ''', (staff['staff_id'], school_id, start_date, end_date)).fetchall()
            
            # Calculate total overtime hours
            total_overtime_hours = 0.0
            for record in overtime_records:
                hours = calculate_overtime_hours(record['overtime_in'], record['overtime_out'])
                total_overtime_hours += hours
            
            overtime_days = len(overtime_records)
            
            # Format overtime details for display
            overtime_details = ""
            if overtime_records:
                details_list = []
                for record in overtime_records:
                    details_list.append(f"{record['date']} ({record['overtime_in']}-{record['overtime_out']})")
                overtime_details = "; ".join(details_list[:3])  # Show max 3 details
                if len(overtime_records) > 3:
                    overtime_details += f" and {len(overtime_records)-3} more..."
            else:
                overtime_details = "No overtime recorded"
            
            # Store data for totals calculation
            corrected_data = {
                'overtime_days': overtime_days,
                'total_hours': total_overtime_hours
            }
            corrected_staff_data.append(corrected_data)
            
            values = [
                staff['staff_id'],
                staff['full_name'],
                staff['department'] or 'Unassigned',
                staff['position'],
                overtime_days,
                f"{total_overtime_hours:.2f}",
                overtime_details
            ]
            
            for col, value in enumerate(values, 1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.border = self.border
                
                # Add conditional formatting
                if col == 5 and overtime_days > 5:  # High overtime days
                    cell.fill = PatternFill(start_color='FFCCCC', end_color='FFCCCC', fill_type='solid')
                elif col == 6 and total_overtime_hours > 20:  # High overtime hours
                    cell.fill = PatternFill(start_color='FFCCCC', end_color='FFCCCC', fill_type='solid')
                elif col == 5 and overtime_days > 0:  # Has overtime
                    cell.fill = PatternFill(start_color='CCFFCC', end_color='CCFFCC', fill_type='solid')
            
            row += 1
        
        # Add summary row
        if corrected_staff_data:
            row += 1
            
            # Calculate totals
            total_staff_with_overtime = len([d for d in corrected_staff_data if d['overtime_days'] > 0])
            total_overtime_days = sum(record['overtime_days'] for record in corrected_staff_data)
            total_overtime_hours = sum(record['total_hours'] for record in corrected_staff_data)
            
            summary_values = [
                "TOTALS:",
                f"{total_staff_with_overtime} Staff with Overtime",
                "",
                "",
                total_overtime_days,
                f"{total_overtime_hours:.2f}",
                f"{total_staff_with_overtime} out of {len(corrected_staff_data)} staff worked overtime"
            ]
            
            for col, value in enumerate(summary_values, 1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.font = Font(bold=True)
                cell.border = self.border
                if col == 1:  # "TOTALS:" label
                    cell.fill = PatternFill(start_color='D3D3D3', end_color='D3D3D3', fill_type='solid')
                else:  # Data cells
                    cell.fill = PatternFill(start_color='E6E6FA', end_color='E6E6FA', fill_type='solid')
        
        # Format columns
        column_widths = [12, 25, 18, 18, 16, 16, 50]
        for col, width in enumerate(column_widths, 1):
            ws.column_dimensions[chr(64 + col)].width = width
        
        # Add notes
        notes_row = row + 3
        ws.cell(row=notes_row, column=1, value="Notes:").font = Font(bold=True)
        ws.cell(row=notes_row + 1, column=1, value=f"• Overtime data for {year}/{month:02d}")
        ws.cell(row=notes_row + 2, column=1, value="• Staff ID sorted in ascending numerical order")
        ws.cell(row=notes_row + 3, column=1, value="• Hours calculated from overtime_in and overtime_out times")
        ws.cell(row=notes_row + 4, column=1, value="• Green highlighting = Staff with overtime recorded")
        ws.cell(row=notes_row + 5, column=1, value="• Red highlighting = High overtime (>5 days or >20 hours)")

    def _create_overtime_summary_sheet(self, wb, school_id, year, month, department=None):
        """Create overtime summary sheet with statistics"""
        ws = wb.create_sheet("Overtime Summary")
        
        # Title
        ws['A1'] = f"Overtime Summary Report - {year}/{month:02d}"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:F1')
        if self.generated_by:
            ws['A2'] = f"Generated by: {self.generated_by}"
        
        db = get_db()
        school = db.execute('SELECT name FROM schools WHERE id = ?', (school_id,)).fetchone()
        ws['A3'] = f"School: {school['name'] if school else 'Unknown'}"
        
        # Monthly statistics
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
        
        # Get overtime statistics
        overtime_stats = db.execute('''
            SELECT
                COUNT(DISTINCT s.id) as total_staff,
                COUNT(DISTINCT CASE WHEN a.overtime_in IS NOT NULL AND a.overtime_out IS NOT NULL THEN s.id END) as staff_with_overtime,
                COUNT(CASE WHEN a.overtime_in IS NOT NULL AND a.overtime_out IS NOT NULL THEN 1 END) as total_overtime_days,
                AVG(CASE 
                    WHEN a.overtime_in IS NOT NULL AND a.overtime_out IS NOT NULL 
                    THEN (strftime('%H', a.overtime_out) * 60 + strftime('%M', a.overtime_out)) - 
                         (strftime('%H', a.overtime_in) * 60 + strftime('%M', a.overtime_in))
                END) / 60.0 as avg_overtime_hours_per_day
            FROM staff s
            LEFT JOIN attendance a ON s.id = a.staff_id 
                AND a.date BETWEEN ? AND ?
                AND a.school_id = ?
            WHERE s.school_id = ? AND s.is_active = 1
        ''', (start_date, end_date, school_id, school_id)).fetchone()
        
        # Summary statistics
        ws['A5'] = "Summary Statistics"
        ws['A5'].font = Font(bold=True, size=12)
        
        stats = [
            ["Total Active Staff", overtime_stats['total_staff'] or 0],
            ["Staff with Overtime", overtime_stats['staff_with_overtime'] or 0],
            ["Total Overtime Days", overtime_stats['total_overtime_days'] or 0],
            ["Average Hours per Overtime Day", f"{overtime_stats['avg_overtime_hours_per_day']:.2f}" if overtime_stats['avg_overtime_hours_per_day'] else "0.00"],
            ["Overtime Coverage %", f"{((overtime_stats['staff_with_overtime'] or 0) / max(overtime_stats['total_staff'], 1) * 100):.1f}%"]
        ]
        
        for row, (label, value) in enumerate(stats, 7):
            ws.cell(row=row, column=1, value=label).font = Font(bold=True)
            ws.cell(row=row, column=2, value=value)
            
            # Add borders
            ws.cell(row=row, column=1).border = self.border
            ws.cell(row=row, column=2).border = self.border
        
        # Format columns
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 15

    def _create_overtime_trends_sheet(self, wb, school_id, year, month):
        """Create overtime trends analysis sheet"""
        ws = wb.create_sheet("Overtime Trends")
        
        # Title
        ws['A1'] = f"Overtime Trends - {year}/{month:02d}"
        ws['A1'].font = self.title_font
        ws.merge_cells('A1:F1')
        
        # Date range
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
        
        db = get_db()
        
        # Department-wise overtime analysis
        dept_overtime = db.execute('''
            SELECT
                COALESCE(s.department, 'Unassigned') as department,
                COUNT(DISTINCT s.id) as total_staff,
                COUNT(DISTINCT CASE WHEN a.overtime_in IS NOT NULL AND a.overtime_out IS NOT NULL THEN s.id END) as staff_with_overtime,
                COUNT(CASE WHEN a.overtime_in IS NOT NULL AND a.overtime_out IS NOT NULL THEN 1 END) as overtime_instances
            FROM staff s
            LEFT JOIN attendance a ON s.id = a.staff_id 
                AND a.date BETWEEN ? AND ?
                AND a.school_id = ?
            WHERE s.school_id = ? AND s.is_active = 1
            GROUP BY s.department
            ORDER BY overtime_instances DESC
        ''', (start_date, end_date, school_id, school_id)).fetchall()
        
        # Department analysis
        ws['A3'] = "Department-wise Overtime Analysis"
        ws['A3'].font = Font(bold=True, size=12)
        
        headers = ['Department', 'Total Staff', 'Staff with OT', 'OT Instances', 'Coverage %']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col)
            cell.value = header
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.border = self.border
        
        for row, dept in enumerate(dept_overtime, 5):
            coverage_pct = (dept['staff_with_overtime'] / max(dept['total_staff'], 1) * 100)
            
            values = [
                dept['department'],
                dept['total_staff'],
                dept['staff_with_overtime'],
                dept['overtime_instances'],
                f"{coverage_pct:.1f}%"
            ]
            
            for col, value in enumerate(values, 1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.border = self.border
                
                # Color coding for coverage
                if col == 5:  # Coverage percentage
                    if coverage_pct >= 50:
                        cell.fill = PatternFill(start_color='FFCCCC', end_color='FFCCCC', fill_type='solid')
                    elif coverage_pct >= 25:
                        cell.fill = PatternFill(start_color='FFFFCC', end_color='FFFFCC', fill_type='solid')
                    else:
                        cell.fill = PatternFill(start_color='CCFFCC', end_color='CCFFCC', fill_type='solid')
        
        # Format columns
        column_widths = [18, 12, 14, 12, 12]
        for col, width in enumerate(column_widths, 1):
            ws.column_dimensions[chr(64 + col)].width = width

    def generate_usage_report(self, report_data, filename):
        """Generate comprehensive leave usage report for an individual staff member"""
        wb = openpyxl.Workbook()
        ws = wb.active
        if ws is not None:
            ws.title = "Leave Usage Summary"
        
        staff_name = report_data['staff_name']
        employee_id = report_data['employee_id']
        department = report_data['department']
        year = report_data['year']
        quota_data = report_data['quota_data']
        usage_records = report_data['usage_records']
        
        # Title Section
        ws['A1'] = f"Leave & Permission Usage Report - {year}"
        ws['A1'].font = Font(bold=True, size=16, color="2F5597")
        ws.merge_cells('A1:G1')
        
        # Staff Information
        ws['A3'] = "Staff Information"
        ws['A3'].font = Font(bold=True, size=12)
        
        info_data = [
            ("Name:", staff_name),
            ("Employee ID:", employee_id),
            ("Department:", department),
            ("Report Year:", year),
            ("Generated On:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        ]
        
        for i, (label, value) in enumerate(info_data, 4):
            ws[f'A{i}'] = label
            ws[f'A{i}'].font = Font(bold=True)
            ws[f'B{i}'] = value
        
        # Quota Summary Section
        start_row = 10
        ws[f'A{start_row}'] = "Quota Summary"
        ws[f'A{start_row}'].font = Font(bold=True, size=12)
        
        # Quota headers
        quota_headers = ['Leave Type', 'Unit', 'Allocated', 'Used', 'Remaining', 'Usage %']
        for col, header in enumerate(quota_headers, 1):
            cell = ws.cell(row=start_row+1, column=col)
            cell.value = header
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.border = self.border
        
        # Quota data
        for row, quota in enumerate(quota_data, start_row+2):
            quota_type, unit, allocated, used, remaining = quota
            usage_pct = (used / max(allocated, 1)) * 100 if allocated > 0 else 0
            
            values = [quota_type, unit, allocated, used, remaining, f"{usage_pct:.1f}%"]
            
            for col, value in enumerate(values, 1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.border = self.border
                
                # Color coding for usage percentage
                if col == 6:  # Usage percentage column
                    if usage_pct >= 90:
                        cell.fill = PatternFill(start_color='FFCCCC', end_color='FFCCCC', fill_type='solid')
                    elif usage_pct >= 70:
                        cell.fill = PatternFill(start_color='FFFFCC', end_color='FFFFCC', fill_type='solid')
                    else:
                        cell.fill = PatternFill(start_color='CCFFCC', end_color='CCFFCC', fill_type='solid')
        
        # Usage Records Section
        usage_start_row = start_row + len(quota_data) + 4
        ws[f'A{usage_start_row}'] = "Usage History"
        ws[f'A{usage_start_row}'].font = Font(bold=True, size=12)
        
        if usage_records:
            # Usage headers
            usage_headers = ['Date Range', 'Type', 'Days/Hours', 'Reason', 'Status', 'Application Type']
            for col, header in enumerate(usage_headers, 1):
                cell = ws.cell(row=usage_start_row+1, column=col)
                cell.value = header
                cell.font = self.header_font
                cell.fill = self.header_fill
                cell.border = self.border
            
            # Usage data
            for row, record in enumerate(usage_records, usage_start_row+2):
                start_date, end_date, days_used, reason, status, quota_type, app_type = record
                
                # Format date range
                if start_date == end_date:
                    date_range = start_date
                else:
                    date_range = f"{start_date} to {end_date}"
                
                values = [
                    date_range,
                    quota_type,
                    days_used,
                    reason or 'N/A',
                    status.title(),
                    app_type
                ]
                
                for col, value in enumerate(values, 1):
                    cell = ws.cell(row=row, column=col, value=value)
                    cell.border = self.border
                    
                    # Color coding for status
                    if col == 5:  # Status column
                        if status.lower() == 'approved':
                            cell.fill = PatternFill(start_color='CCFFCC', end_color='CCFFCC', fill_type='solid')
                        elif status.lower() == 'pending':
                            cell.fill = PatternFill(start_color='FFFFCC', end_color='FFFFCC', fill_type='solid')
                        elif status.lower() == 'rejected':
                            cell.fill = PatternFill(start_color='FFCCCC', end_color='FFCCCC', fill_type='solid')
        else:
            ws[f'A{usage_start_row+2}'] = "No usage records found for this year."
            ws[f'A{usage_start_row+2}'].font = Font(italic=True, color="666666")
        
        # Format column widths
        column_widths = [16, 12, 10, 10, 12, 12, 14]
        for col, width in enumerate(column_widths, 1):
            ws.column_dimensions[chr(64 + col)].width = width
        
        # Add summary statistics at the bottom
        stats_row = usage_start_row + len(usage_records) + 5 if usage_records else usage_start_row + 5
        ws[f'A{stats_row}'] = "Summary Statistics"
        ws[f'A{stats_row}'].font = Font(bold=True, size=12)
        
        # Calculate totals separately for days and hours
        total_allocated_days = sum(quota[2] for quota in quota_data if quota[1].lower() == 'days')
        total_used_days = sum(quota[3] for quota in quota_data if quota[1].lower() == 'days')
        total_remaining_days = sum(quota[4] for quota in quota_data if quota[1].lower() == 'days')
        
        total_allocated_hours = sum(quota[2] for quota in quota_data if quota[1].lower() == 'hours')
        total_used_hours = sum(quota[3] for quota in quota_data if quota[1].lower() == 'hours')
        total_remaining_hours = sum(quota[4] for quota in quota_data if quota[1].lower() == 'hours')
        
        # Calculate overall usage percentage for days
        overall_usage_pct_days = (total_used_days / max(total_allocated_days, 1)) * 100 if total_allocated_days > 0 else 0
        overall_usage_pct_hours = (total_used_hours / max(total_allocated_hours, 1)) * 100 if total_allocated_hours > 0 else 0
        
        stats_data = [
            ("Days - Allocated:", f"{total_allocated_days} days"),
            ("Days - Used:", f"{total_used_days} days"),
            ("Days - Remaining:", f"{total_remaining_days} days"),
            ("Days - Usage %:", f"{overall_usage_pct_days:.1f}%")
        ]
        
        # Add hours statistics if there are any hour-based quotas
        if total_allocated_hours > 0:
            stats_data.extend([
                ("Hours - Allocated:", f"{total_allocated_hours} hours"),
                ("Hours - Used:", f"{total_used_hours} hours"),
                ("Hours - Remaining:", f"{total_remaining_hours} hours"),
                ("Hours - Usage %:", f"{overall_usage_pct_hours:.1f}%")
            ])
        
        for i, (label, value) in enumerate(stats_data, stats_row+1):
            ws[f'A{i}'] = label
            ws[f'A{i}'].font = Font(bold=True)
            ws[f'B{i}'] = value
            if 'Usage %:' in label:
                usage_val = float(str(value).replace('%', ''))
                if usage_val >= 80:
                    ws[f'B{i}'].fill = PatternFill(start_color='FFCCCC', end_color='FFCCCC', fill_type='solid')
                elif usage_val >= 60:
                    ws[f'B{i}'].fill = PatternFill(start_color='FFFFCC', end_color='FFFFCC', fill_type='solid')
        
        return self._save_workbook_to_response(wb, filename)
