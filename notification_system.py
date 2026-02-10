# notification_system.py
"""
Comprehensive Notification System

This module provides notification capabilities including:
- Email notifications
- In-app notifications
- SMS notifications (optional)
- Push notifications
- Attendance alerts
- Leave approval notifications
- System updates
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from database import get_db
import os
from flask import current_app


class NotificationManager:
    """Comprehensive notification management system"""
    
    def __init__(self):
        self.email_config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'email': os.getenv('SYSTEM_EMAIL', 'noreply@vishnorex.com'),
            'password': os.getenv('EMAIL_PASSWORD', ''),
            'use_tls': True
        }
        
        self.notification_types = [
            'attendance_alert', 'leave_approval', 'leave_rejection',
            'late_arrival', 'absent_alert', 'overtime_alert',
            'system_update', 'password_reset', 'account_created'
        ]
    
    def send_email_notification(self, to_email: str, subject: str, 
                              body: str, html_body: str = None, 
                              attachments: List[str] = None) -> Dict:
        """Send email notification"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_config['email']
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text body
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML body if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Add attachments if provided
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {os.path.basename(file_path)}'
                            )
                            msg.attach(part)
            
            # Send email
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            if self.email_config['use_tls']:
                server.starttls()
            
            if self.email_config['password']:
                server.login(self.email_config['email'], self.email_config['password'])
            
            server.send_message(msg)
            server.quit()
            
            # Log notification
            self._log_notification('email', to_email, subject, 'sent')
            
            return {'success': True, 'message': 'Email sent successfully'}
            
        except Exception as e:
            self._log_notification('email', to_email, subject, 'failed', str(e))
            return {'success': False, 'error': str(e)}
    
    def create_in_app_notification(self, user_id: int, user_type: str, 
                                 title: str, message: str, 
                                 notification_type: str = 'info',
                                 action_url: str = None) -> Dict:
        """Create in-app notification"""
        try:
            db = get_db()
            
            cursor = db.execute('''
                INSERT INTO notifications (
                    user_id, user_type, title, message, notification_type,
                    action_url, created_at, is_read
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, user_type, title, message, notification_type,
                  action_url, datetime.now(), False))
            
            notification_id = cursor.lastrowid
            db.commit()
            
            return {
                'success': True,
                'notification_id': notification_id,
                'message': 'In-app notification created'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def send_attendance_alert(self, staff_id: int, alert_type: str, 
                            details: Dict = None) -> Dict:
        """Send attendance-related alerts"""
        try:
            db = get_db()
            
            # Get staff and admin details
            staff = db.execute('''
                SELECT s.*, sc.name as school_name, sc.email as school_email
                FROM staff s
                JOIN schools sc ON s.school_id = sc.id
                WHERE s.id = ?
            ''', (staff_id,)).fetchone()
            
            if not staff:
                return {'success': False, 'error': 'Staff not found'}
            
            # Get admin emails
            admins = db.execute('''
                SELECT email FROM admins WHERE school_id = ? AND email IS NOT NULL
            ''', (staff['school_id'],)).fetchall()
            
            admin_emails = [admin['email'] for admin in admins if admin['email']]
            
            # Prepare notification content based on alert type
            if alert_type == 'late_arrival':
                subject = f"Late Arrival Alert - {staff['full_name']}"
                body = f"""
                Dear Admin,
                
                Staff member {staff['full_name']} (ID: {staff['staff_id']}) 
                arrived late today at {details.get('time_in', 'N/A')}.
                
                Late by: {details.get('late_minutes', 0)} minutes
                Department: {staff['department'] or 'N/A'}
                
                Please take necessary action.
                
                Best regards,
                VishnoRex Attendance System
                """
                
            elif alert_type == 'absent_alert':
                subject = f"Absence Alert - {staff['full_name']}"
                body = f"""
                Dear Admin,
                
                Staff member {staff['full_name']} (ID: {staff['staff_id']}) 
                is marked absent for {details.get('date', 'today')}.
                
                Department: {staff['department'] or 'N/A'}
                
                Please verify and take necessary action.
                
                Best regards,
                VishnoRex Attendance System
                """
                
            elif alert_type == 'overtime_alert':
                subject = f"Overtime Alert - {staff['full_name']}"
                body = f"""
                Dear Admin,
                
                Staff member {staff['full_name']} (ID: {staff['staff_id']}) 
                has worked overtime today.
                
                Overtime hours: {details.get('overtime_hours', 0)} hours
                Department: {staff['department'] or 'N/A'}
                
                Please review and approve if necessary.
                
                Best regards,
                VishnoRex Attendance System
                """
            
            # Send emails to admins
            results = []
            for admin_email in admin_emails:
                result = self.send_email_notification(admin_email, subject, body)
                results.append(result)
            
            # Create in-app notification for staff
            if alert_type == 'late_arrival':
                self.create_in_app_notification(
                    staff_id, 'staff',
                    'Late Arrival Recorded',
                    f'You arrived late today at {details.get("time_in", "N/A")}. Late by {details.get("late_minutes", 0)} minutes.',
                    'warning'
                )
            
            return {
                'success': True,
                'emails_sent': len([r for r in results if r['success']]),
                'total_emails': len(admin_emails)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def send_leave_notification(self, leave_id: int, action: str, 
                              admin_reason: str = None) -> Dict:
        """Send leave approval/rejection notifications"""
        try:
            db = get_db()
            
            # Get leave application details
            leave = db.execute('''
                SELECT l.*, s.full_name, s.email, s.staff_id,
                       sc.name as school_name
                FROM leave_applications l
                JOIN staff s ON l.staff_id = s.id
                JOIN schools sc ON l.school_id = sc.id
                WHERE l.id = ?
            ''', (leave_id,)).fetchone()
            
            if not leave:
                return {'success': False, 'error': 'Leave application not found'}
            
            # Prepare notification content
            if action == 'approved':
                subject = f"Leave Application Approved - {leave['leave_type']}"
                body = f"""
                Dear {leave['full_name']},
                
                Your leave application has been APPROVED.
                
                Leave Details:
                - Type: {leave['leave_type']}
                - From: {leave['start_date']}
                - To: {leave['end_date']}
                - Days: {leave['days_requested']}
                - Reason: {leave['reason']}
                
                {f"Admin Note: {admin_reason}" if admin_reason else ""}
                
                Please ensure proper handover before your leave.
                
                Best regards,
                {leave['school_name']} Administration
                """
                notification_type = 'success'
                
            else:  # rejected
                subject = f"Leave Application Rejected - {leave['leave_type']}"
                body = f"""
                Dear {leave['full_name']},
                
                Your leave application has been REJECTED.
                
                Leave Details:
                - Type: {leave['leave_type']}
                - From: {leave['start_date']}
                - To: {leave['end_date']}
                - Days: {leave['days_requested']}
                - Reason: {leave['reason']}
                
                {f"Rejection Reason: {admin_reason}" if admin_reason else ""}
                
                Please contact administration for more details.
                
                Best regards,
                {leave['school_name']} Administration
                """
                notification_type = 'danger'
            
            # Send email to staff
            email_result = {'success': True}
            if leave['email']:
                email_result = self.send_email_notification(leave['email'], subject, body)
            
            # Create in-app notification
            in_app_result = self.create_in_app_notification(
                leave['staff_id'], 'staff',
                f'Leave Application {action.title()}',
                f'Your {leave["leave_type"]} leave application has been {action}.',
                notification_type,
                '/staff_dashboard'
            )
            
            return {
                'success': True,
                'email_sent': email_result['success'],
                'in_app_created': in_app_result['success']
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def send_system_notification(self, user_type: str, title: str, 
                               message: str, school_id: int = None) -> Dict:
        """Send system-wide notifications"""
        try:
            db = get_db()
            
            # Get users based on type and school
            if user_type == 'all':
                users = db.execute('''
                    SELECT id, 'admin' as type FROM admins WHERE school_id = ?
                    UNION ALL
                    SELECT id, 'staff' as type FROM staff WHERE school_id = ?
                ''', (school_id, school_id)).fetchall()
            elif user_type == 'admin':
                users = db.execute('''
                    SELECT id, 'admin' as type FROM admins WHERE school_id = ?
                ''', (school_id,)).fetchall()
            elif user_type == 'staff':
                users = db.execute('''
                    SELECT id, 'staff' as type FROM staff WHERE school_id = ?
                ''', (school_id,)).fetchall()
            else:
                return {'success': False, 'error': 'Invalid user type'}
            
            # Create notifications for all users
            notifications_created = 0
            for user in users:
                result = self.create_in_app_notification(
                    user['id'], user['type'], title, message, 'info'
                )
                if result['success']:
                    notifications_created += 1
            
            return {
                'success': True,
                'notifications_created': notifications_created,
                'total_users': len(users)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_user_notifications(self, user_id: int, user_type: str, 
                             limit: int = 50, unread_only: bool = False) -> Dict:
        """Get notifications for a user"""
        try:
            db = get_db()
            
            where_clause = 'WHERE user_id = ? AND user_type = ?'
            params = [user_id, user_type]
            
            if unread_only:
                where_clause += ' AND is_read = 0'
            
            notifications = db.execute(f'''
                SELECT * FROM notifications
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ?
            ''', params + [limit]).fetchall()
            
            return {
                'success': True,
                'notifications': [dict(notification) for notification in notifications],
                'count': len(notifications)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def mark_notification_read(self, notification_id: int, user_id: int) -> Dict:
        """Mark notification as read"""
        try:
            db = get_db()
            
            db.execute('''
                UPDATE notifications 
                SET is_read = 1, read_at = ?
                WHERE id = ? AND user_id = ?
            ''', (datetime.now(), notification_id, user_id))
            
            db.commit()
            
            return {'success': True, 'message': 'Notification marked as read'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _log_notification(self, notification_type: str, recipient: str, 
                         subject: str, status: str, error: str = None):
        """Log notification for debugging and tracking"""
        try:
            db = get_db()
            
            db.execute('''
                INSERT INTO notification_logs (
                    notification_type, recipient, subject, status, error, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (notification_type, recipient, subject, status, error, datetime.now()))
            
            db.commit()
            
        except Exception as e:
            print(f"Error logging notification: {e}")
    
    def cleanup_old_notifications(self, days_old: int = 30) -> Dict:
        """Clean up old notifications"""
        try:
            db = get_db()
            
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            # Delete old notifications
            result = db.execute('''
                DELETE FROM notifications 
                WHERE created_at < ? AND is_read = 1
            ''', (cutoff_date,))
            
            deleted_count = result.rowcount
            
            # Delete old logs
            db.execute('''
                DELETE FROM notification_logs 
                WHERE created_at < ?
            ''', (cutoff_date,))
            
            db.commit()
            
            return {
                'success': True,
                'deleted_notifications': deleted_count,
                'message': f'Cleaned up notifications older than {days_old} days'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
