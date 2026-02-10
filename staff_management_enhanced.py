# staff_management_enhanced.py
"""
Enhanced Staff Management Module

This module provides advanced staff management features including:
- Bulk operations (import/export, bulk updates)
- Advanced search and filtering
- Staff photo management
- Department-wise management
- Staff analytics and reporting
- Automated staff onboarding
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename
from PIL import Image
import io
import base64
from database import get_db
from flask import current_app
import csv
from typing import List, Dict, Optional, Tuple


class StaffManager:
    """Enhanced staff management with advanced features"""
    
    def __init__(self):
        self.allowed_photo_extensions = {'png', 'jpg', 'jpeg', 'gif'}
        self.max_photo_size = 5 * 1024 * 1024  # 5MB
        self.photo_dimensions = (300, 300)  # Standard photo size
    
    def bulk_import_staff(self, file_path: str, school_id: int) -> Dict:
        """Import staff from Excel/CSV file"""
        try:
            # Read file based on extension
            if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                df = pd.read_excel(file_path)
            elif file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                return {'success': False, 'error': 'Unsupported file format'}
            
            # Validate required columns
            required_columns = ['staff_id', 'full_name', 'email', 'phone', 'department']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return {'success': False, 'error': f'Missing columns: {", ".join(missing_columns)}'}
            
            db = get_db()
            imported_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Check if staff already exists
                    existing = db.execute(
                        'SELECT id FROM staff WHERE school_id = ? AND staff_id = ?',
                        (school_id, row['staff_id'])
                    ).fetchone()
                    
                    if existing:
                        errors.append(f"Row {index + 2}: Staff ID {row['staff_id']} already exists")
                        continue
                    
                    # Insert new staff member
                    db.execute('''
                        INSERT INTO staff (
                            school_id, staff_id, full_name, email, phone, department,
                            position, gender, date_of_birth, date_of_joining, password
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        school_id,
                        row['staff_id'],
                        row['full_name'],
                        row.get('email', ''),
                        row.get('phone', ''),
                        row.get('department', ''),
                        row.get('position', ''),
                        row.get('gender', ''),
                        row.get('date_of_birth', ''),
                        row.get('date_of_joining', datetime.now().strftime('%Y-%m-%d')),
                        'password123'  # Default password
                    ))
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {index + 2}: {str(e)}")
            
            db.commit()
            
            return {
                'success': True,
                'imported_count': imported_count,
                'errors': errors,
                'total_rows': len(df)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def bulk_update_staff(self, updates: List[Dict], school_id: int) -> Dict:
        """Bulk update staff members"""
        try:
            db = get_db()
            updated_count = 0
            errors = []
            
            for update in updates:
                try:
                    staff_id = update.get('staff_id')
                    if not staff_id:
                        errors.append("Missing staff_id in update")
                        continue
                    
                    # Build update query dynamically
                    update_fields = []
                    update_values = []
                    
                    for field, value in update.items():
                        if field != 'staff_id' and value is not None:
                            update_fields.append(f"{field} = ?")
                            update_values.append(value)
                    
                    if update_fields:
                        query = f"UPDATE staff SET {', '.join(update_fields)} WHERE school_id = ? AND id = ?"
                        update_values.extend([school_id, staff_id])
                        
                        result = db.execute(query, update_values)
                        if result.rowcount > 0:
                            updated_count += 1
                        else:
                            errors.append(f"Staff ID {staff_id} not found")
                    
                except Exception as e:
                    errors.append(f"Error updating staff ID {update.get('staff_id', 'unknown')}: {str(e)}")
            
            db.commit()
            
            return {
                'success': True,
                'updated_count': updated_count,
                'errors': errors,
                'total_updates': len(updates)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def advanced_search_staff(self, school_id: int, filters: Dict) -> List[Dict]:
        """Advanced search with multiple filters"""
        db = get_db()
        
        # Build dynamic query
        where_conditions = ['school_id = ?']
        params = [school_id]
        
        if filters.get('search_term'):
            where_conditions.append('''
                (full_name LIKE ? OR staff_id LIKE ? OR email LIKE ? OR phone LIKE ?)
            ''')
            search_term = f"%{filters['search_term']}%"
            params.extend([search_term, search_term, search_term, search_term])
        
        if filters.get('department'):
            where_conditions.append('department = ?')
            params.append(filters['department'])
        
        if filters.get('position'):
            # Check both position and destination columns for backward compatibility
            where_conditions.append('(position = ? OR destination = ?)')
            params.append(filters['position'])
            params.append(filters['position'])
        
        if filters.get('gender'):
            where_conditions.append('gender = ?')
            params.append(filters['gender'])
        
        # Build final query
        query = f'''
            SELECT * FROM staff
            WHERE {' AND '.join(where_conditions)}
            ORDER BY full_name
        '''

        # Only apply limit if explicitly provided
        if filters.get('limit') and filters['limit'].strip():
            try:
                limit_value = int(filters['limit'])
                if limit_value > 0:
                    query += f" LIMIT {limit_value}"
            except (ValueError, TypeError):
                pass  # Ignore invalid limit values
        
        staff_members = db.execute(query, params).fetchall()
        return [dict(staff) for staff in staff_members]
    
    def manage_staff_photo(self, staff_id: int, photo_file) -> Dict:
        """Upload and manage staff photos"""
        try:
            if not photo_file:
                return {'success': False, 'error': 'No photo file provided'}
            
            # Validate file extension
            filename = secure_filename(photo_file.filename)
            if not filename or '.' not in filename:
                return {'success': False, 'error': 'Invalid filename'}
            
            file_ext = filename.rsplit('.', 1)[1].lower()
            if file_ext not in self.allowed_photo_extensions:
                return {'success': False, 'error': 'Invalid file type. Allowed: PNG, JPG, JPEG, GIF'}
            
            # Check file size
            photo_file.seek(0, 2)  # Seek to end
            file_size = photo_file.tell()
            photo_file.seek(0)  # Reset to beginning
            
            if file_size > self.max_photo_size:
                return {'success': False, 'error': 'File too large. Maximum size: 5MB'}
            
            # Process image
            image = Image.open(photo_file)
            
            # Resize image
            image.thumbnail(self.photo_dimensions, Image.Resampling.LANCZOS)
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')
            
            # Save to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG', quality=85)
            img_byte_arr = img_byte_arr.getvalue()
            
            # Encode to base64
            photo_data = base64.b64encode(img_byte_arr).decode('utf-8')
            
            # Save to database
            db = get_db()
            db.execute('''
                UPDATE staff SET photo_data = ? WHERE id = ?
            ''', (photo_data, staff_id))
            db.commit()
            
            return {
                'success': True,
                'message': 'Photo uploaded successfully',
                'photo_data': f"data:image/jpeg;base64,{photo_data}"
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_department_analytics(self, school_id: int) -> Dict:
        """Get department-wise staff analytics"""
        db = get_db()
        
        # Department distribution
        dept_stats = db.execute('''
            SELECT 
                COALESCE(department, 'Unassigned') as department,
                COUNT(*) as staff_count,
                COUNT(CASE WHEN gender = 'Male' THEN 1 END) as male_count,
                COUNT(CASE WHEN gender = 'Female' THEN 1 END) as female_count,
                AVG(CASE WHEN date_of_joining IS NOT NULL THEN 
                    (julianday('now') - julianday(date_of_joining)) / 365.25 
                END) as avg_tenure_years
            FROM staff 
            WHERE school_id = ?
            GROUP BY department
            ORDER BY staff_count DESC
        ''', (school_id,)).fetchall()
        
        # Age distribution
        age_stats = db.execute('''
            SELECT 
                CASE 
                    WHEN date_of_birth IS NULL THEN 'Unknown'
                    WHEN (julianday('now') - julianday(date_of_birth)) / 365.25 < 25 THEN 'Under 25'
                    WHEN (julianday('now') - julianday(date_of_birth)) / 365.25 < 35 THEN '25-34'
                    WHEN (julianday('now') - julianday(date_of_birth)) / 365.25 < 45 THEN '35-44'
                    WHEN (julianday('now') - julianday(date_of_birth)) / 365.25 < 55 THEN '45-54'
                    ELSE '55+'
                END as age_group,
                COUNT(*) as count
            FROM staff 
            WHERE school_id = ?
            GROUP BY age_group
            ORDER BY 
                CASE age_group
                    WHEN 'Under 25' THEN 1
                    WHEN '25-34' THEN 2
                    WHEN '35-44' THEN 3
                    WHEN '45-54' THEN 4
                    WHEN '55+' THEN 5
                    ELSE 6
                END
        ''', (school_id,)).fetchall()
        
        # Recent joinings (last 30 days)
        recent_joinings = db.execute('''
            SELECT COUNT(*) as count
            FROM staff 
            WHERE school_id = ? AND date_of_joining >= date('now', '-30 days')
        ''', (school_id,)).fetchone()
        
        return {
            'department_stats': [dict(row) for row in dept_stats],
            'age_distribution': [dict(row) for row in age_stats],
            'recent_joinings': recent_joinings['count'],
            'total_staff': sum(row['staff_count'] for row in dept_stats)
        }
    
    def generate_staff_id(self, school_id: int, department: str = None) -> str:
        """Generate unique staff ID"""
        db = get_db()
        
        # Get school prefix
        school = db.execute('SELECT name FROM schools WHERE id = ?', (school_id,)).fetchone()
        school_prefix = school['name'][:3].upper() if school else 'SCH'
        
        # Get department prefix
        dept_prefix = department[:2].upper() if department else 'GN'
        
        # Get next sequence number
        existing_ids = db.execute('''
            SELECT staff_id FROM staff 
            WHERE school_id = ? AND staff_id LIKE ?
            ORDER BY staff_id DESC
        ''', (school_id, f"{school_prefix}{dept_prefix}%")).fetchall()
        
        if existing_ids:
            # Extract number from last ID and increment
            last_id = existing_ids[0]['staff_id']
            try:
                last_num = int(last_id[-4:])  # Last 4 digits
                next_num = last_num + 1
            except:
                next_num = 1
        else:
            next_num = 1
        
        return f"{school_prefix}{dept_prefix}{next_num:04d}"
