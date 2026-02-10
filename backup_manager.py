# backup_manager.py
"""
Backup and Data Management System

This module provides comprehensive backup and data management features including:
- Database backup and restore
- Data export/import
- Data archiving
- Automated backup scheduling
- Data integrity checks
- Backup compression and encryption
"""

import sqlite3
import shutil
import os
import json
import zipfile
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from database import get_db
import pandas as pd
import threading
from pathlib import Path


class BackupManager:
    """Comprehensive backup and data management system"""
    
    def __init__(self):
        self.backup_dir = 'backups'
        self.archive_dir = 'archives'
        self.export_dir = 'exports'
        self.temp_dir = 'temp'
        
        # Create directories if they don't exist
        for directory in [self.backup_dir, self.archive_dir, self.export_dir, self.temp_dir]:
            os.makedirs(directory, exist_ok=True)
        
        self.backup_retention_days = 30
        self.archive_retention_days = 365
    
    def create_database_backup(self, backup_name: str = None, 
                             include_logs: bool = True) -> Dict:
        """Create a complete database backup"""
        try:
            if not backup_name:
                backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            backup_path = os.path.join(self.backup_dir, f"{backup_name}.db")
            
            # Create backup using SQLite backup API
            source_db = get_db()
            backup_db = sqlite3.connect(backup_path)
            
            # Perform the backup
            source_db.backup(backup_db)
            backup_db.close()
            
            # Get backup file size
            backup_size = os.path.getsize(backup_path)
            
            # Create backup metadata
            metadata = {
                'backup_name': backup_name,
                'backup_path': backup_path,
                'backup_size': backup_size,
                'created_at': datetime.now().isoformat(),
                'include_logs': include_logs,
                'database_version': self._get_database_version(),
                'table_counts': self._get_table_counts()
            }
            
            # Save metadata
            metadata_path = os.path.join(self.backup_dir, f"{backup_name}_metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Log backup creation
            self._log_backup_operation('create', backup_name, 'success')
            
            return {
                'success': True,
                'backup_name': backup_name,
                'backup_path': backup_path,
                'backup_size': backup_size,
                'metadata': metadata
            }
            
        except Exception as e:
            self._log_backup_operation('create', backup_name or 'unknown', 'failed', str(e))
            return {'success': False, 'error': str(e)}
    
    def restore_database_backup(self, backup_name: str, 
                              confirm_restore: bool = False) -> Dict:
        """Restore database from backup"""
        try:
            if not confirm_restore:
                return {
                    'success': False,
                    'error': 'Restore confirmation required. This will overwrite current database.'
                }
            
            backup_path = os.path.join(self.backup_dir, f"{backup_name}.db")
            
            if not os.path.exists(backup_path):
                return {'success': False, 'error': 'Backup file not found'}
            
            # Create a backup of current database before restore
            current_backup = self.create_database_backup(f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            # Get current database path
            current_db_path = 'vishnorex.db'  # Adjust based on your database file name
            
            # Close current database connections
            # Note: In production, you'd need to handle this more carefully
            
            # Replace current database with backup
            shutil.copy2(backup_path, current_db_path)
            
            # Verify restore
            verification_result = self._verify_database_integrity()
            
            if verification_result['success']:
                self._log_backup_operation('restore', backup_name, 'success')
                return {
                    'success': True,
                    'message': 'Database restored successfully',
                    'pre_restore_backup': current_backup.get('backup_name'),
                    'verification': verification_result
                }
            else:
                # Restore failed, revert to pre-restore backup
                if current_backup['success']:
                    shutil.copy2(current_backup['backup_path'], current_db_path)
                
                return {
                    'success': False,
                    'error': 'Database restore failed verification',
                    'verification_error': verification_result.get('error')
                }
            
        except Exception as e:
            self._log_backup_operation('restore', backup_name, 'failed', str(e))
            return {'success': False, 'error': str(e)}
    
    def export_data(self, export_type: str, school_id: int = None, 
                   start_date: str = None, end_date: str = None,
                   tables: List[str] = None) -> Dict:
        """Export data in various formats"""
        try:
            export_name = f"export_{export_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            export_path = os.path.join(self.export_dir, export_name)
            
            if export_type == 'excel':
                return self._export_to_excel(export_path, school_id, start_date, end_date, tables)
            elif export_type == 'csv':
                return self._export_to_csv(export_path, school_id, start_date, end_date, tables)
            elif export_type == 'json':
                return self._export_to_json(export_path, school_id, start_date, end_date, tables)
            elif export_type == 'complete':
                return self._export_complete_data(export_path, school_id)
            else:
                return {'success': False, 'error': 'Invalid export type'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _export_to_excel(self, export_path: str, school_id: int = None,
                        start_date: str = None, end_date: str = None,
                        tables: List[str] = None) -> Dict:
        """Export data to Excel format"""
        try:
            db = get_db()
            excel_path = f"{export_path}.xlsx"
            
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                # Export staff data
                if not tables or 'staff' in tables:
                    staff_query = 'SELECT * FROM staff'
                    params = []
                    if school_id:
                        staff_query += ' WHERE school_id = ?'
                        params.append(school_id)
                    
                    staff_df = pd.read_sql_query(staff_query, db, params=params)
                    staff_df.to_excel(writer, sheet_name='Staff', index=False)
                
                # Export attendance data
                if not tables or 'attendance' in tables:
                    attendance_query = '''
                        SELECT a.*, s.full_name, s.staff_id, s.department
                        FROM attendance a
                        JOIN staff s ON a.staff_id = s.id
                    '''
                    params = []
                    conditions = []
                    
                    if school_id:
                        conditions.append('a.school_id = ?')
                        params.append(school_id)
                    
                    if start_date and end_date:
                        conditions.append('a.date BETWEEN ? AND ?')
                        params.extend([start_date, end_date])
                    
                    if conditions:
                        attendance_query += ' WHERE ' + ' AND '.join(conditions)
                    
                    attendance_query += ' ORDER BY a.date DESC, s.full_name'
                    
                    attendance_df = pd.read_sql_query(attendance_query, db, params=params)
                    attendance_df.to_excel(writer, sheet_name='Attendance', index=False)
                
                # Export leave applications
                if not tables or 'leave_applications' in tables:
                    leave_query = '''
                        SELECT l.*, s.full_name, s.staff_id, s.department
                        FROM leave_applications l
                        JOIN staff s ON l.staff_id = s.id
                    '''
                    params = []
                    if school_id:
                        leave_query += ' WHERE l.school_id = ?'
                        params.append(school_id)
                    
                    leave_query += ' ORDER BY l.applied_at DESC'
                    
                    leave_df = pd.read_sql_query(leave_query, db, params=params)
                    leave_df.to_excel(writer, sheet_name='Leave Applications', index=False)
            
            file_size = os.path.getsize(excel_path)
            
            return {
                'success': True,
                'export_path': excel_path,
                'export_size': file_size,
                'export_type': 'excel'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _export_to_csv(self, export_path: str, school_id: int = None,
                      start_date: str = None, end_date: str = None,
                      tables: List[str] = None) -> Dict:
        """Export data to CSV format"""
        try:
            db = get_db()
            csv_dir = f"{export_path}_csv"
            os.makedirs(csv_dir, exist_ok=True)
            
            exported_files = []
            
            # Export each table to separate CSV
            export_tables = tables or ['staff', 'attendance', 'leave_applications']
            
            for table in export_tables:
                if table == 'staff':
                    query = 'SELECT * FROM staff'
                    params = []
                    if school_id:
                        query += ' WHERE school_id = ?'
                        params.append(school_id)
                
                elif table == 'attendance':
                    query = '''
                        SELECT a.*, s.full_name, s.staff_id, s.department
                        FROM attendance a
                        JOIN staff s ON a.staff_id = s.id
                    '''
                    params = []
                    conditions = []
                    
                    if school_id:
                        conditions.append('a.school_id = ?')
                        params.append(school_id)
                    
                    if start_date and end_date:
                        conditions.append('a.date BETWEEN ? AND ?')
                        params.extend([start_date, end_date])
                    
                    if conditions:
                        query += ' WHERE ' + ' AND '.join(conditions)
                
                elif table == 'leave_applications':
                    query = '''
                        SELECT l.*, s.full_name, s.staff_id, s.department
                        FROM leave_applications l
                        JOIN staff s ON l.staff_id = s.id
                    '''
                    params = []
                    if school_id:
                        query += ' WHERE l.school_id = ?'
                        params.append(school_id)
                
                # Execute query and save to CSV
                df = pd.read_sql_query(query, db, params=params)
                csv_path = os.path.join(csv_dir, f"{table}.csv")
                df.to_csv(csv_path, index=False)
                exported_files.append(csv_path)
            
            # Create ZIP file with all CSVs
            zip_path = f"{export_path}.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in exported_files:
                    zipf.write(file_path, os.path.basename(file_path))
            
            # Clean up individual CSV files
            shutil.rmtree(csv_dir)
            
            file_size = os.path.getsize(zip_path)
            
            return {
                'success': True,
                'export_path': zip_path,
                'export_size': file_size,
                'export_type': 'csv_zip',
                'files_exported': len(exported_files)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def archive_old_data(self, archive_before_date: str, 
                        tables: List[str] = None) -> Dict:
        """Archive old data to reduce database size"""
        try:
            db = get_db()
            archive_name = f"archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            archive_path = os.path.join(self.archive_dir, f"{archive_name}.db")
            
            # Create archive database
            archive_db = sqlite3.connect(archive_path)
            
            # Copy table structures
            tables_to_archive = tables or ['attendance', 'leave_applications', 'notification_logs']
            archived_counts = {}
            
            for table in tables_to_archive:
                # Get table schema
                schema_query = f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'"
                schema = db.execute(schema_query).fetchone()
                
                if schema:
                    # Create table in archive database
                    archive_db.execute(schema['sql'])
                    
                    # Copy old data
                    if table == 'attendance':
                        copy_query = f"SELECT * FROM {table} WHERE date < ?"
                    elif table == 'leave_applications':
                        copy_query = f"SELECT * FROM {table} WHERE applied_at < ?"
                    elif table == 'notification_logs':
                        copy_query = f"SELECT * FROM {table} WHERE created_at < ?"
                    else:
                        copy_query = f"SELECT * FROM {table} WHERE created_at < ?"
                    
                    old_data = db.execute(copy_query, (archive_before_date,)).fetchall()
                    
                    if old_data:
                        # Get column names
                        columns = [description[0] for description in db.execute(f"SELECT * FROM {table} LIMIT 1").description]
                        placeholders = ','.join(['?' for _ in columns])
                        
                        # Insert into archive
                        archive_db.executemany(
                            f"INSERT INTO {table} VALUES ({placeholders})",
                            old_data
                        )
                        
                        # Delete from main database
                        if table == 'attendance':
                            delete_query = f"DELETE FROM {table} WHERE date < ?"
                        elif table == 'leave_applications':
                            delete_query = f"DELETE FROM {table} WHERE applied_at < ?"
                        elif table == 'notification_logs':
                            delete_query = f"DELETE FROM {table} WHERE created_at < ?"
                        else:
                            delete_query = f"DELETE FROM {table} WHERE created_at < ?"
                        
                        result = db.execute(delete_query, (archive_before_date,))
                        archived_counts[table] = result.rowcount
            
            archive_db.commit()
            archive_db.close()
            db.commit()
            
            # Create archive metadata
            metadata = {
                'archive_name': archive_name,
                'archive_path': archive_path,
                'archive_date': datetime.now().isoformat(),
                'archived_before': archive_before_date,
                'tables_archived': tables_to_archive,
                'record_counts': archived_counts,
                'archive_size': os.path.getsize(archive_path)
            }
            
            metadata_path = os.path.join(self.archive_dir, f"{archive_name}_metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return {
                'success': True,
                'archive_name': archive_name,
                'archived_counts': archived_counts,
                'total_archived': sum(archived_counts.values()),
                'archive_size': metadata['archive_size']
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_database_version(self) -> str:
        """Get database version/schema version"""
        try:
            db = get_db()
            # You can implement a version table or use PRAGMA user_version
            version = db.execute('PRAGMA user_version').fetchone()[0]
            return str(version)
        except:
            return "unknown"
    
    def _get_table_counts(self) -> Dict:
        """Get record counts for all tables"""
        try:
            db = get_db()
            tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            counts = {}
            
            for table in tables:
                table_name = table['name']
                count = db.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                counts[table_name] = count
            
            return counts
        except Exception as e:
            return {'error': str(e)}
    
    def _verify_database_integrity(self) -> Dict:
        """Verify database integrity"""
        try:
            db = get_db()
            
            # Run integrity check
            integrity_result = db.execute('PRAGMA integrity_check').fetchone()[0]
            
            if integrity_result == 'ok':
                return {'success': True, 'message': 'Database integrity verified'}
            else:
                return {'success': False, 'error': f'Integrity check failed: {integrity_result}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _log_backup_operation(self, operation: str, backup_name: str, 
                            status: str, error: str = None):
        """Log backup operations"""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'operation': operation,
                'backup_name': backup_name,
                'status': status,
                'error': error
            }
            
            log_file = os.path.join(self.backup_dir, 'backup_log.json')
            
            # Read existing log
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    log_data = json.load(f)
            else:
                log_data = []
            
            # Add new entry
            log_data.append(log_entry)
            
            # Keep only last 1000 entries
            if len(log_data) > 1000:
                log_data = log_data[-1000:]
            
            # Write back to file
            with open(log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
                
        except Exception as e:
            print(f"Error logging backup operation: {e}")
    
    def cleanup_old_backups(self) -> Dict:
        """Clean up old backup files"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.backup_retention_days)
            deleted_files = []
            
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.db') or filename.endswith('_metadata.json'):
                    file_path = os.path.join(self.backup_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    
                    if file_time < cutoff_date:
                        os.remove(file_path)
                        deleted_files.append(filename)
            
            return {
                'success': True,
                'deleted_files': deleted_files,
                'deleted_count': len(deleted_files)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
