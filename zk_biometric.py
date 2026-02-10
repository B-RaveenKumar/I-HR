#!/usr/bin/env python3
"""
ZK Biometric Device Integration Module
Handles connection to ZK biometric devices and attendance data synchronization
Now supports both direct Ethernet and cloud-based connectivity
"""

from zk import ZK, const
import pymysql
import sqlite3
import datetime
import logging
import requests
import json
from typing import List, Dict, Optional
from database import get_db
from flask import current_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import cloud modules (with fallback for backward compatibility)
try:
    from cloud_config import get_cloud_config, get_device_config
    from cloud_connector import get_cloud_connector
    CLOUD_ENABLED = True
except ImportError:
    logger.warning("Cloud modules not available. Running in Ethernet-only mode.")
    CLOUD_ENABLED = False

class ZKBiometricDevice:
    """ZK Biometric Device Handler - supports both Ethernet and Cloud connectivity"""

    def __init__(self, device_ip: str = '192.168.1.21', port: int = 4370, timeout: int = 5,
                 device_id: str = None, use_cloud: bool = None):
        self.device_ip = device_ip
        self.port = port
        self.timeout = timeout
        self.device_id = device_id or f"ZK_{device_ip.replace('.', '_')}"

        # Determine connection mode
        if use_cloud is None:
            # Auto-detect based on cloud availability and configuration
            self.use_cloud = CLOUD_ENABLED and self._should_use_cloud()
        else:
            self.use_cloud = use_cloud and CLOUD_ENABLED

        # Initialize connection objects
        if not self.use_cloud:
            # Direct Ethernet connection
            self.zk = ZK(device_ip, port=port, timeout=timeout)
            self.connection = None
        else:
            # Cloud connection
            self.zk = None
            self.connection = None
            self.cloud_connector = get_cloud_connector() if CLOUD_ENABLED else None

        logger.info(f"ZK Device {self.device_id} initialized in {'cloud' if self.use_cloud else 'ethernet'} mode")

    def _should_use_cloud(self) -> bool:
        """Determine if cloud connectivity should be used"""
        if not CLOUD_ENABLED:
            return False

        try:
            config = get_cloud_config()
            device_config = get_device_config(self.device_id)

            # Use cloud if device is configured for cloud and cloud is enabled
            return (device_config and device_config.cloud_enabled and
                   config.api_base_url and config.api_key)
        except:
            return False

    def connect(self) -> bool:
        """Connect to ZK device (Ethernet or Cloud)"""
        if self.use_cloud:
            return self._connect_cloud()
        else:
            return self._connect_ethernet()

    def _connect_ethernet(self) -> bool:
        """Connect to ZK device via Ethernet"""
        try:
            self.connection = self.zk.connect()
            logger.info(f"Successfully connected to ZK device at {self.device_ip} via Ethernet")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to ZK device via Ethernet: {str(e)}")
            return False

    def _connect_cloud(self) -> bool:
        """Connect to ZK device via Cloud"""
        try:
            if not self.cloud_connector:
                logger.error("Cloud connector not available")
                return False

            # Check if cloud connector is running
            if not self.cloud_connector.running:
                logger.error("Cloud connector is not running")
                return False

            # Test cloud connectivity by getting device status
            status = self.cloud_connector.get_device_status(self.device_id)
            if status['status'] in ['connected', 'disconnected']:
                logger.info(f"Successfully connected to ZK device {self.device_id} via Cloud")
                self.connection = True  # Mark as connected for cloud mode
                return True
            else:
                logger.error(f"Device {self.device_id} not available via cloud: {status['status']}")
                return False

        except Exception as e:
            logger.error(f"Failed to connect to ZK device via Cloud: {str(e)}")
            return False

    def disconnect(self):
        """Disconnect from ZK device"""
        if self.use_cloud:
            self._disconnect_cloud()
        else:
            self._disconnect_ethernet()

    def _disconnect_ethernet(self):
        """Disconnect from ZK device via Ethernet"""
        if self.connection:
            try:
                self.connection.disconnect()
                logger.info("Disconnected from ZK device via Ethernet")
            except Exception as e:
                logger.error(f"Error disconnecting from ZK device via Ethernet: {str(e)}")

    def _disconnect_cloud(self):
        """Disconnect from ZK device via Cloud"""
        # For cloud mode, we don't need to explicitly disconnect
        # The cloud connector manages the connection
        self.connection = None
        logger.info(f"Disconnected from ZK device {self.device_id} via Cloud")

    def get_attendance_records(self) -> List[Dict]:
        """Get attendance records from ZK device (Ethernet or Cloud)"""
        if self.use_cloud:
            return self._get_attendance_records_cloud()
        else:
            return self._get_attendance_records_ethernet()

    def _get_attendance_records_ethernet(self) -> List[Dict]:
        """Get attendance records from ZK device via Ethernet"""
        if not self.connection:
            logger.error("No connection to ZK device")
            return []

        try:
            # Disable device to prevent interference
            self.connection.disable_device()

            # Get attendance records
            attendance = self.connection.get_attendance()
            records = []

            for record in attendance:
                # Map punch codes to our verification types
                verification_type = self._map_punch_to_verification_type(record.punch)

                records.append({
                    'user_id': record.user_id,
                    'timestamp': record.timestamp,
                    'status': record.status,
                    'punch': record.punch,  # Original punch code
                    'verification_type': verification_type,  # Mapped verification type
                    'verify': getattr(record, 'verify', 0)  # Verification method (safe access)
                })

            # Re-enable device
            self.connection.enable_device()

            logger.info(f"Retrieved {len(records)} attendance records from ZK device via Ethernet")
            return records

        except Exception as e:
            logger.error(f"Error getting attendance records via Ethernet: {str(e)}")
            # Make sure to re-enable device even if error occurs
            try:
                self.connection.enable_device()
            except:
                pass
            return []

    def _get_attendance_records_cloud(self) -> List[Dict]:
        """Get attendance records from ZK device via Cloud"""
        try:
            if not self.cloud_connector:
                logger.error("Cloud connector not available")
                return []

            # Make API request to get attendance records
            response = self.cloud_connector.send_cloud_api_request(
                f'devices/{self.device_id}/attendance',
                method='GET'
            )

            if response and response.get('success'):
                records = response.get('records', [])

                # Convert ISO timestamp strings back to datetime objects
                for record in records:
                    if 'timestamp' in record and isinstance(record['timestamp'], str):
                        try:
                            record['timestamp'] = datetime.datetime.fromisoformat(record['timestamp'])
                        except ValueError:
                            logger.warning(f"Invalid timestamp format: {record['timestamp']}")

                logger.info(f"Retrieved {len(records)} attendance records from ZK device via Cloud")
                return records
            else:
                logger.error(f"Failed to get attendance records via Cloud: {response}")
                return []

        except Exception as e:
            logger.error(f"Error getting attendance records via Cloud: {str(e)}")
            return []

    def _map_punch_to_verification_type(self, punch_code: int) -> str:
        """
        Map ZK device punch codes to our verification types

        ZK Device punch codes:
        0 = Check In -> check-in
        1 = Check Out -> check-out
        2 = Break Out -> overtime-in (repurposed for overtime start)
        3 = Break In -> overtime-out (repurposed for overtime end)

        Args:
            punch_code: The punch code from ZK device

        Returns:
            String verification type
        """
        punch_mapping = {
            0: 'check-in',
            1: 'check-out',
            2: 'overtime-in',
            3: 'overtime-out'
        }

        return punch_mapping.get(punch_code, 'check-in')  # Default to check-in

    def get_new_attendance_records(self, since_timestamp: datetime.datetime = None) -> List[Dict]:
        """
        Get attendance records from ZK device since a specific timestamp

        Args:
            since_timestamp: Only return records after this timestamp

        Returns:
            List of attendance records
        """
        all_records = self.get_attendance_records()

        if since_timestamp is None:
            return all_records

        # Filter records to only include those after the specified timestamp
        new_records = []
        for record in all_records:
            if record['timestamp'] > since_timestamp:
                new_records.append(record)

        return new_records

    def process_device_attendance_to_database(self, school_id: int = 1) -> Dict:
        """
        Process attendance records from device and update database automatically

        Args:
            school_id: School ID for the attendance records

        Returns:
            Dict with processing results
        """
        result = {
            'success': False,
            'processed_count': 0,
            'errors': [],
            'message': ''
        }

        try:
            # Get all attendance records from device
            records = self.get_attendance_records()

            if not records:
                result['message'] = 'No attendance records found on device'
                result['success'] = True
                return result

            # Get database connection
            db = get_db()

            processed_count = 0

            for record in records:
                try:
                    # Check if this record has already been processed
                    existing_verification = db.execute('''
                        SELECT id FROM biometric_verifications
                        WHERE staff_id = ? AND verification_time = ? AND verification_type = ?
                    ''', (record['user_id'], record['timestamp'], record['verification_type'])).fetchone()

                    if existing_verification:
                        continue  # Skip already processed records

                    # Validate staff exists
                    staff = db.execute('SELECT id FROM staff WHERE staff_id = ?', (record['user_id'],)).fetchone()
                    if not staff:
                        result['errors'].append(f"Staff ID {record['user_id']} not found in database")
                        continue

                    staff_db_id = staff['id']

                    # Process the attendance record
                    self._process_single_attendance_record(db, staff_db_id, school_id, record)
                    processed_count += 1

                except Exception as e:
                    result['errors'].append(f"Error processing record for user {record['user_id']}: {str(e)}")
                    logger.error(f"Error processing attendance record: {str(e)}")

            db.commit()

            result['success'] = True
            result['processed_count'] = processed_count
            result['message'] = f"Successfully processed {processed_count} attendance records"

            logger.info(f"Processed {processed_count} attendance records from device")

        except Exception as e:
            result['errors'].append(f"Database error: {str(e)}")
            result['message'] = f"Failed to process attendance records: {str(e)}"
            logger.error(f"Error processing device attendance: {str(e)}")

        return result

    def _process_single_attendance_record(self, db, staff_db_id: int, school_id: int, record: Dict):
        """
        Process a single attendance record and update the database

        Args:
            db: Database connection
            staff_db_id: Staff database ID
            school_id: School ID
            record: Attendance record from device
        """
        verification_type = record['verification_type']
        timestamp = record['timestamp']
        current_time = timestamp.strftime('%H:%M:%S')
        today = timestamp.date()

        # Log the biometric verification
        db.execute('''
            INSERT INTO biometric_verifications
            (staff_id, school_id, verification_type, verification_time, device_ip, biometric_method, verification_status)
            VALUES (?, ?, ?, ?, ?, 'fingerprint', 'success')
        ''', (staff_db_id, school_id, verification_type, timestamp, self.device_ip))

        # Get existing attendance record for today
        existing_attendance = db.execute('''
            SELECT * FROM attendance WHERE staff_id = ? AND date = ?
        ''', (staff_db_id, today)).fetchone()

        # Use ShiftManager for strict timing and late duration computation
        from shift_management import ShiftManager

        if verification_type == 'check-in':
            # DUPLICATE CHECK-IN PREVENTION: Only allow first check-in of the day
            if existing_attendance and existing_attendance['time_in']:
                logger.warning(f"Duplicate check-in attempt blocked for staff {staff_db_id} on {today}. Original check-in: {existing_attendance['time_in']}, attempted: {current_time}")
                print(f"🚫 DUPLICATE CHECK-IN BLOCKED: Staff {staff_db_id} already checked in at {existing_attendance['time_in']}, attempted again at {current_time}")
                return  # Skip this duplicate check-in
            
            # Get staff department and shift for accurate status calculation
            staff_info = db.execute('''
                SELECT department, COALESCE(shift_type, 'general') AS shift_type
                FROM staff WHERE id = ?
            ''', (staff_db_id,)).fetchone()

            department = staff_info['department'] if staff_info else None
            shift_type = staff_info['shift_type'] if staff_info else 'general'

            # Calculate status and late minutes strictly vs shift start
            shift_manager = ShiftManager()
            attendance_result = shift_manager.calculate_attendance_status(
                shift_type, timestamp.time()
            )
            status = attendance_result['status']
            late_minutes = attendance_result.get('late_duration_minutes', 0)
            shift_start = attendance_result.get('shift_start_time')
            shift_end = attendance_result.get('shift_end_time')

            print(f"🔍 BIOMETRIC DEBUG: Check-in at {timestamp.time()} for shift {shift_type}")
            print(f"🔍 BIOMETRIC DEBUG: Status = {status}, Late minutes = {late_minutes}")

            if existing_attendance:
                # Only update if there's no existing check-in time (this shouldn't happen due to check above, but safety net)
                if not existing_attendance['time_in']:
                    db.execute('''
                        UPDATE attendance SET time_in = ?, status = ?, late_duration_minutes = ?,
                            shift_start_time = ?, shift_end_time = ?
                        WHERE staff_id = ? AND date = ?
                    ''', (
                        current_time, status, late_minutes,
                        shift_start.strftime('%H:%M:%S') if shift_start else None,
                        shift_end.strftime('%H:%M:%S') if shift_end else None,
                        staff_db_id, today
                    ))
            else:
                # Create new record including late minutes and shift bounds
                db.execute('''
                    INSERT INTO attendance (staff_id, school_id, date, time_in, status,
                                            late_duration_minutes, shift_start_time, shift_end_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    staff_db_id, school_id, today, current_time, status,
                    late_minutes,
                    shift_start.strftime('%H:%M:%S') if shift_start else None,
                    shift_end.strftime('%H:%M:%S') if shift_end else None
                ))

        elif verification_type == 'check-out':
            # DUPLICATE CHECK-OUT PREVENTION: Only allow first check-out of the day
            if existing_attendance and existing_attendance['time_out']:
                logger.warning(f"Duplicate check-out attempt blocked for staff {staff_db_id} on {today}. Original check-out: {existing_attendance['time_out']}, attempted: {current_time}")
                print(f"🚫 DUPLICATE CHECK-OUT BLOCKED: Staff {staff_db_id} already checked out at {existing_attendance['time_out']}, attempted again at {current_time}")
                return  # Skip this duplicate check-out
            
            # Check-out verification with early departure detection
            if existing_attendance:
                # Get the actual check-in time from existing attendance record
                check_in_time = None
                if existing_attendance['time_in']:
                    try:
                        check_in_time = datetime.datetime.strptime(existing_attendance['time_in'], '%H:%M:%S').time()
                    except (ValueError, TypeError):
                        check_in_time = None

                # Use ShiftManager for check-out status calculation
                shift_manager = ShiftManager()
                staff_info = db.execute('''
                    SELECT COALESCE(shift_type, 'general') AS shift_type
                    FROM staff WHERE id = ?
                ''', (staff_db_id,)).fetchone()

                shift_type = staff_info['shift_type'] if staff_info else 'general'
                
                # Calculate early departure if check-in time is available
                early_departure_minutes = 0
                if check_in_time:
                    checkout_result = shift_manager.calculate_attendance_status(
                        shift_type, check_in_time, timestamp.time()  # proper check_in and check_out times
                    )
                    early_departure_minutes = checkout_result.get('early_departure_minutes', 0)

                if early_departure_minutes > 0:
                    # Early departure detected
                    db.execute('''
                        UPDATE attendance SET time_out = ?, early_departure_minutes = ?
                        WHERE staff_id = ? AND date = ?
                    ''', (current_time, early_departure_minutes, staff_db_id, today))
                    print(f"🔍 CHECKOUT DEBUG: Early departure detected: {early_departure_minutes} minutes")
                else:
                    # Normal check-out, just update time_out
                    db.execute('''
                        UPDATE attendance SET time_out = ?
                        WHERE staff_id = ? AND date = ?
                    ''', (current_time, staff_db_id, today))
                    print(f"🔍 CHECKOUT DEBUG: Normal checkout updated: {current_time}")
            else:
                logger.warning(f"Check-out attempt without check-in for staff {staff_db_id} on {today}")
                print(f"⚠️ CHECK-OUT WITHOUT CHECK-IN: Staff {staff_db_id} attempted check-out at {current_time} without checking in first")

        elif verification_type == 'overtime-in':
            # Overtime-in verification
            if existing_attendance:
                db.execute('''
                    UPDATE attendance SET overtime_in = ?
                    WHERE staff_id = ? AND date = ?
                ''', (current_time, staff_db_id, today))

        elif verification_type == 'overtime-out':
            # Overtime-out verification
            if existing_attendance:
                db.execute('''
                    UPDATE attendance SET overtime_out = ?
                    WHERE staff_id = ? AND date = ?
                ''', (current_time, staff_db_id, today))
    
    def get_users(self) -> List[Dict]:
        """Get users from ZK device (Ethernet or Cloud)"""
        if self.use_cloud:
            return self._get_users_cloud()
        else:
            return self._get_users_ethernet()

    def _get_users_ethernet(self) -> List[Dict]:
        """Get users from ZK device via Ethernet"""
        if not self.connection:
            logger.error("No connection to ZK device")
            return []

        try:
            users = self.connection.get_users()
            user_list = []

            for user in users:
                # Handle both dict and object formats
                if isinstance(user, dict):
                    user_list.append(user)
                else:
                    user_list.append({
                        'uid': getattr(user, 'uid', 0),
                        'user_id': getattr(user, 'user_id', ''),
                        'name': getattr(user, 'name', ''),
                        'privilege': getattr(user, 'privilege', 0),
                        'password': getattr(user, 'password', ''),
                        'group_id': getattr(user, 'group_id', '0')
                    })

            logger.info(f"Retrieved {len(user_list)} users from ZK device via Ethernet")
            return user_list

        except Exception as e:
            logger.error(f"Error getting users via Ethernet: {str(e)}")
            return []

    def _get_users_cloud(self) -> List[Dict]:
        """Get users from ZK device via Cloud"""
        try:
            if not self.cloud_connector:
                logger.error("Cloud connector not available")
                return []

            # Make API request to get users
            response = self.cloud_connector.send_cloud_api_request(
                f'devices/{self.device_id}/users',
                method='GET'
            )

            if response and response.get('success'):
                users = response.get('users', [])
                logger.info(f"Retrieved {len(users)} users from ZK device via Cloud")
                return users
            else:
                logger.error(f"Failed to get users via Cloud: {response}")
                return []

        except Exception as e:
            logger.error(f"Error getting users via Cloud: {str(e)}")
            return []
    
    def clear_attendance(self) -> bool:
        """Clear attendance records from ZK device"""
        if not self.connection:
            logger.error("No connection to ZK device")
            return False

        try:
            self.connection.clear_attendance()
            logger.info("Cleared attendance records from ZK device")
            return True
        except Exception as e:
            logger.error(f"Error clearing attendance: {str(e)}")
            return False

    def enroll_user(self, user_id: str, name: str, privilege: int = 0, password: str = '', group_id: str = '0', overwrite: bool = False) -> dict:
        """Enroll a new user in the ZK device (Ethernet or Cloud)"""
        if self.use_cloud:
            return self._enroll_user_cloud(user_id, name, privilege, password, group_id, overwrite)
        else:
            return self._enroll_user_ethernet(user_id, name, privilege, password, group_id, overwrite)

    def _enroll_user_ethernet(self, user_id: str, name: str, privilege: int = 0, password: str = '', group_id: str = '0', overwrite: bool = False) -> dict:
        """Enroll a new user in the ZK device via Ethernet"""
        if not self.connection:
            logger.error("No connection to ZK device")
            return {'success': False, 'message': 'No connection to ZK device', 'user_exists': False}

        try:
            # Disable device during enrollment
            self.connection.disable_device()

            # Check if user already exists
            existing_users = self.connection.get_users()
            existing_user = None
            for user in existing_users:
                # Handle both dict and object formats
                user_id_value = user.get('user_id') if isinstance(user, dict) else getattr(user, 'user_id', None)
                if str(user_id_value) == str(user_id):
                    existing_user = user
                    break

            if existing_user:
                if not overwrite:
                    logger.warning(f"User {user_id} already exists on device")
                    self.connection.enable_device()
                    return {
                        'success': False,
                        'message': f'User {user_id} already exists on device',
                        'user_exists': True,
                        'existing_user': {
                            'user_id': existing_user.get('user_id') if isinstance(existing_user, dict) else getattr(existing_user, 'user_id', 'Unknown'),
                            'name': existing_user.get('name') if isinstance(existing_user, dict) else getattr(existing_user, 'name', 'Unknown'),
                            'privilege': existing_user.get('privilege') if isinstance(existing_user, dict) else getattr(existing_user, 'privilege', 0)
                        }
                    }
                else:
                    # Delete existing user first
                    logger.info(f"Overwriting existing user {user_id}")
                    self.connection.delete_user(existing_user.uid)

            # Get next available UID
            users = self.connection.get_users()
            max_uid = max([user.uid for user in users] + [0]) + 1

            # Create user object using the correct approach for pyzk
            try:
                # Try different approaches for user creation based on pyzk version
                try:
                    # Method 1: Direct set_user call (newer pyzk versions)
                    self.connection.set_user(
                        uid=int(max_uid),
                        name=str(name),
                        privilege=int(privilege),
                        password=str(password) if password else '',
                        group_id=str(group_id) if group_id else '0',
                        user_id=str(user_id)
                    )
                    logger.info(f"User created with UID {max_uid} using direct set_user")

                except Exception as direct_error:
                    logger.warning(f"Direct set_user failed: {direct_error}")

                    # Method 2: Using User class (older pyzk versions)
                    try:
                        from zk.user import User
                        new_user = User(
                            uid=int(max_uid),
                            name=str(name),
                            privilege=int(privilege),
                            password=str(password) if password else '',
                            group_id=str(group_id) if group_id else '0',
                            user_id=str(user_id)
                        )
                        self.connection.set_user(new_user)
                        logger.info(f"User created with UID {max_uid} using User class")

                    except Exception as class_error:
                        logger.warning(f"User class creation failed: {class_error}")

                        # Method 3: Minimal user creation
                        try:
                            # Some devices only need basic parameters
                            self.connection.set_user(
                                uid=int(max_uid),
                                name=str(name),
                                user_id=str(user_id)
                            )
                            logger.info(f"User created with UID {max_uid} using minimal parameters")
                        except Exception as minimal_error:
                            raise Exception(f"All user creation methods failed: {minimal_error}")

            except Exception as user_error:
                logger.error(f"Failed to create user object: {user_error}")
                # Re-enable device and return error
                self.connection.enable_device()
                return {'success': False, 'message': f'Failed to create user: {str(user_error)}', 'user_exists': False}

            # Re-enable device
            self.connection.enable_device()

            action = "overwritten" if existing_user else "enrolled"
            logger.info(f"Successfully {action} user {user_id} ({name}) on ZK device")
            return {
                'success': True,
                'message': f'User {user_id} successfully {action} on device',
                'user_exists': existing_user is not None,
                'action': action
            }

        except Exception as e:
            logger.error(f"Error enrolling user {user_id}: {str(e)}")
            # Make sure to re-enable device
            try:
                self.connection.enable_device()
            except:
                pass
            return {'success': False, 'message': f'Error enrolling user: {str(e)}', 'user_exists': False}

    def _enroll_user_cloud(self, user_id: str, name: str, privilege: int = 0, password: str = '', group_id: str = '0', overwrite: bool = False) -> dict:
        """Enroll a new user in the ZK device via Cloud"""
        try:
            if not self.cloud_connector:
                logger.error("Cloud connector not available")
                return {'success': False, 'message': 'Cloud connector not available', 'user_exists': False}

            # Prepare enrollment data
            data = {
                'command': 'enroll_user',
                'user_id': user_id,
                'name': name,
                'privilege': privilege,
                'password': password,
                'group_id': group_id,
                'overwrite': overwrite
            }

            # Send enrollment command via cloud API
            response = self.cloud_connector.send_cloud_api_request(
                f'devices/{self.device_id}/command',
                method='POST',
                data=data
            )

            if response and response.get('success'):
                action = "enrolled"
                logger.info(f"Successfully {action} user {user_id} ({name}) on ZK device via Cloud")
                return {
                    'success': True,
                    'message': response.get('message', f'User {user_id} successfully {action} on device'),
                    'user_exists': False,  # Cloud API handles this
                    'action': action
                }
            else:
                error_msg = response.get('message', 'Unknown error') if response else 'No response from cloud API'
                logger.error(f"Failed to enroll user {user_id} via Cloud: {error_msg}")
                return {'success': False, 'message': error_msg, 'user_exists': False}

        except Exception as e:
            logger.error(f"Error enrolling user {user_id} via Cloud: {str(e)}")
            return {'success': False, 'message': f'Error enrolling user via Cloud: {str(e)}', 'user_exists': False}

    def delete_user(self, user_id: str) -> bool:
        """Delete a user from the ZK device (Ethernet or Cloud)"""
        if self.use_cloud:
            return self._delete_user_cloud(user_id)
        else:
            return self._delete_user_ethernet(user_id)

    def _delete_user_ethernet(self, user_id: str) -> bool:
        """Delete a user from the ZK device via Ethernet"""
        if not self.connection:
            logger.error("No connection to ZK device")
            return False

        try:
            # Disable device during deletion
            self.connection.disable_device()

            # Find and delete user
            users = self.connection.get_users()
            for user in users:
                # Handle both dict and object formats
                user_id_value = user.get('user_id') if isinstance(user, dict) else getattr(user, 'user_id', None)
                if str(user_id_value) == str(user_id):
                    user_uid = user.get('uid') if isinstance(user, dict) else getattr(user, 'uid', None)
                    self.connection.delete_user(user_uid)
                    logger.info(f"Successfully deleted user {user_id} from ZK device")
                    self.connection.enable_device()
                    return True

            # Re-enable device
            self.connection.enable_device()
            logger.warning(f"User {user_id} not found on device")
            return False

        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {str(e)}")
            # Make sure to re-enable device
            try:
                self.connection.enable_device()
            except:
                pass
            return False

    def _delete_user_cloud(self, user_id: str) -> bool:
        """Delete a user from the ZK device via Cloud"""
        try:
            if not self.cloud_connector:
                logger.error("Cloud connector not available")
                return False

            # Prepare deletion data
            data = {
                'command': 'delete_user',
                'user_id': user_id
            }

            # Send deletion command via cloud API
            response = self.cloud_connector.send_cloud_api_request(
                f'devices/{self.device_id}/command',
                method='POST',
                data=data
            )

            if response and response.get('success'):
                logger.info(f"Successfully deleted user {user_id} from ZK device via Cloud")
                return True
            else:
                error_msg = response.get('message', 'Unknown error') if response else 'No response from cloud API'
                logger.error(f"Failed to delete user {user_id} via Cloud: {error_msg}")
                return False

        except Exception as e:
            logger.error(f"Error deleting user {user_id} via Cloud: {str(e)}")
            return False

    def start_enrollment_mode(self, user_id: str = None) -> bool:
        """Put device in enrollment mode for biometric capture"""
        if not self.connection:
            logger.error("No connection to ZK device")
            return False

        try:
            # Disable device to prevent normal operation during enrollment
            self.connection.disable_device()

            # Try to trigger enrollment mode using available ZK commands
            try:
                # Some ZK devices support direct enrollment commands
                # This will vary by device model and firmware
                if hasattr(self.connection, 'start_enroll'):
                    # If the device supports start_enroll command
                    if user_id:
                        self.connection.start_enroll(user_id)
                    else:
                        self.connection.start_enroll()
                    logger.info(f"Started enrollment mode for user {user_id if user_id else 'new user'}")
                elif hasattr(self.connection, 'enroll_user'):
                    # Alternative enrollment method
                    logger.info("Using alternative enrollment method")
                else:
                    # Fallback: Use device beep and voice prompts if available
                    if hasattr(self.connection, 'test_voice'):
                        try:
                            self.connection.test_voice()  # Voice prompt for enrollment
                        except:
                            pass

                    # Enable device temporarily to allow manual enrollment
                    self.connection.enable_device()
                    logger.info("Device enabled for manual biometric enrollment")
                    logger.info("Please use the device interface to enroll biometric data")
                    return True

            except Exception as enrollment_error:
                logger.warning(f"Direct enrollment command failed: {enrollment_error}")
                # Fallback to manual enrollment mode
                self.connection.enable_device()
                logger.info("Device enabled for manual biometric enrollment")

            logger.info("Device set to enrollment mode")
            return True

        except Exception as e:
            logger.error(f"Error setting enrollment mode: {str(e)}")
            # Make sure device is re-enabled if error occurs
            try:
                self.connection.enable_device()
            except:
                pass
            return False

    def end_enrollment_mode(self) -> bool:
        """Exit enrollment mode and return to normal operation"""
        if not self.connection:
            logger.error("No connection to ZK device")
            return False

        try:
            # Stop any ongoing enrollment process
            try:
                if hasattr(self.connection, 'cancel_capture'):
                    self.connection.cancel_capture()
                elif hasattr(self.connection, 'stop_enroll'):
                    self.connection.stop_enroll()
            except Exception as stop_error:
                logger.warning(f"Could not stop enrollment process: {stop_error}")

            # Re-enable device for normal operation
            self.connection.enable_device()
            logger.info("Device returned to normal mode")
            return True
        except Exception as e:
            logger.error(f"Error ending enrollment mode: {str(e)}")
            return False

    def trigger_biometric_enrollment(self, user_id: str) -> dict:
        """Trigger biometric enrollment for a specific user"""
        if not self.connection:
            logger.error("No connection to ZK device")
            return {'success': False, 'message': 'No connection to ZK device'}

        try:
            # Disable device during enrollment setup
            self.connection.disable_device()

            # Check if user exists (with retry for newly created users)
            target_user = None
            max_retries = 3

            for attempt in range(max_retries):
                users = self.connection.get_users()
                for user in users:
                    # Handle both dict and object formats
                    user_id_value = user.get('user_id') if isinstance(user, dict) else getattr(user, 'user_id', None)
                    if str(user_id_value) == str(user_id):
                        target_user = user
                        break

                if target_user:
                    break

                if attempt < max_retries - 1:
                    logger.info(f"User {user_id} not found, retrying... (attempt {attempt + 1}/{max_retries})")
                    import time
                    time.sleep(1)  # Wait 1 second before retry

            if not target_user:
                self.connection.enable_device()
                return {'success': False, 'message': f'User {user_id} not found on device after {max_retries} attempts'}

            # Try different enrollment methods based on device capabilities
            enrollment_started = False

            try:
                # Method 1: Direct enrollment command with user ID
                if hasattr(self.connection, 'start_enroll'):
                    self.connection.start_enroll(target_user.uid)
                    enrollment_started = True
                    logger.info(f"Started enrollment for user {user_id} using start_enroll")

                # Method 2: Alternative enrollment methods
                elif hasattr(self.connection, 'enroll_user'):
                    self.connection.enroll_user(target_user.uid)
                    enrollment_started = True
                    logger.info(f"Started enrollment for user {user_id} using enroll_user")

                # Method 3: Capture finger method
                elif hasattr(self.connection, 'capture_finger'):
                    self.connection.capture_finger()
                    enrollment_started = True
                    logger.info(f"Started finger capture for user {user_id}")

            except Exception as enroll_error:
                logger.warning(f"Direct enrollment methods failed: {enroll_error}")

            if not enrollment_started:
                # Fallback: Enable device and use voice/beep prompts
                try:
                    if hasattr(self.connection, 'test_voice'):
                        self.connection.test_voice()
                    elif hasattr(self.connection, 'beep'):
                        # Beep pattern to indicate enrollment mode
                        for _ in range(3):
                            self.connection.beep()
                except:
                    pass

                self.connection.enable_device()
                logger.info(f"Device enabled for manual enrollment of user {user_id}")
                return {
                    'success': True,
                    'message': f'Device ready for manual biometric enrollment of user {user_id}. Please use device interface.',
                    'manual_mode': True
                }

            # Keep device disabled during enrollment
            return {
                'success': True,
                'message': f'Biometric enrollment started for user {user_id}. Please follow device prompts.',
                'manual_mode': False
            }

        except Exception as e:
            logger.error(f"Error triggering enrollment for user {user_id}: {str(e)}")
            # Make sure device is re-enabled
            try:
                self.connection.enable_device()
            except:
                pass
            return {'success': False, 'message': f'Error triggering enrollment: {str(e)}'}

class AttendanceSync:
    """Synchronize attendance data between ZK device and databases"""
    
    def __init__(self, mysql_config: Optional[Dict] = None):
        self.mysql_config = mysql_config or {
            'host': 'localhost',
            'user': 'root',
            'password': 'yourpass',
            'database': 'staff',
            'port': 3306,
            'connect_timeout': 5,
            'read_timeout': 10,
            'write_timeout': 10
        }
    
    def sync_to_sqlite(self, records: List[Dict], school_id: int = 1) -> int:
        """Sync attendance records to SQLite database"""
        synced_count = 0
        
        try:
            # Use Flask app context to get database connection
            with current_app.app_context():
                db = get_db()
                
                for record in records:
                    try:
                        # Map ZK user_id to staff_id in our system
                        staff = db.execute('''
                            SELECT id FROM staff WHERE staff_id = ? AND school_id = ?
                        ''', (record['user_id'], school_id)).fetchone()
                        
                        if not staff:
                            logger.warning(f"Staff with ID {record['user_id']} not found in school {school_id}")
                            continue
                        
                        staff_id = staff['id']
                        date = record['timestamp'].date()
                        time_val = record['timestamp'].time()

                        # AUTOMATIC SYNC: Handle both check-in and check-out from ZK device
                        if record['punch'] == 0:  # Check In
                            # Check if record already exists
                            existing = db.execute('''
                                SELECT id FROM attendance
                                WHERE staff_id = ? AND date = ?
                            ''', (staff_id, date)).fetchone()

                            if not existing:
                                # Get staff department for holiday checking
                                staff_info = db.execute('''
                                    SELECT department FROM staff WHERE id = ?
                                ''', (staff_id,)).fetchone()

                                department = staff_info['department'] if staff_info else None

                                # Use dynamic institution timings and holiday checking for status calculation
                                from database import calculate_attendance_status
                                status = calculate_attendance_status(time_val, 'check-in',
                                                                   date_obj=datetime.strptime(date, '%Y-%m-%d').date(),
                                                                   department=department)

                                # Convert time to string format for SQLite
                                time_str = time_val.strftime('%H:%M:%S')

                                db.execute('''
                                    INSERT INTO attendance (staff_id, school_id, date, time_in, status)
                                    VALUES (?, ?, ?, ?, ?)
                                ''', (staff_id, school_id, date, time_str, status))
                                synced_count += 1

                        elif record['punch'] == 1:  # Check Out - AUTO SYNC ENABLED
                            # Check if attendance record exists for check-out update
                            existing = db.execute('''
                                SELECT id, time_out FROM attendance
                                WHERE staff_id = ? AND date = ?
                            ''', (staff_id, date)).fetchone()

                            if existing:
                                # Only update if no check-out time exists yet (prevent overwriting)
                                if not existing['time_out']:
                                    # Convert time to string format for SQLite
                                    time_str = time_val.strftime('%H:%M:%S')

                                    db.execute('''
                                        UPDATE attendance
                                        SET time_out = ?
                                        WHERE staff_id = ? AND date = ?
                                    ''', (time_str, staff_id, date))
                                    synced_count += 1
                                    logger.info(f"Auto-synced check-out time {time_str} for staff {staff_id} on {date}")
                            else:
                                # No check-in record found, log warning but don't create orphan check-out
                                logger.warning(f"Check-out sync skipped: No check-in record found for staff {staff_id} on {date}")

                        # Note: Overtime-in (punch == 4) and overtime-out (punch == 5) remain manual only
                        
                    except Exception as e:
                        logger.error(f"Error syncing record {record}: {str(e)}")
                        continue
                
                db.commit()
                logger.info(f"Synced {synced_count} records to SQLite database")
                
        except Exception as e:
            logger.error(f"Error syncing to SQLite: {str(e)}")
        
        return synced_count
    
    def sync_to_mysql(self, records: List[Dict]) -> int:
        """Sync attendance records to MySQL database"""
        synced_count = 0

        try:
            # Test MySQL connection first
            logger.info("Attempting to connect to MySQL database...")
            conn_db = pymysql.connect(**self.mysql_config)
            cursor = conn_db.cursor()
            logger.info("Successfully connected to MySQL database")

            # Create table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance_log (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    staff_id VARCHAR(50) NOT NULL,
                    timestamp DATETIME NOT NULL,
                    status INT NOT NULL,
                    punch_type INT NOT NULL,
                    verify_method INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_staff_timestamp (staff_id, timestamp)
                )
            ''')

            for record in records:
                try:
                    query = """
                        INSERT INTO attendance_log (staff_id, timestamp, status, punch_type, verify_method)
                        VALUES (%s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                        status = VALUES(status),
                        punch_type = VALUES(punch_type),
                        verify_method = VALUES(verify_method)
                    """
                    cursor.execute(query, (
                        record['user_id'],
                        record['timestamp'],
                        record['status'],
                        record['punch'],
                        record['verify']
                    ))
                    synced_count += 1

                except Exception as e:
                    logger.error(f"Error syncing record to MySQL {record}: {str(e)}")
                    continue

            conn_db.commit()
            cursor.close()
            conn_db.close()

            logger.info(f"Synced {synced_count} records to MySQL database")

        except pymysql.Error as e:
            logger.warning(f"MySQL database not available or connection failed: {str(e)}")
            logger.info("Continuing with SQLite sync only...")
        except Exception as e:
            logger.error(f"Unexpected error syncing to MySQL: {str(e)}")

        return synced_count

def verify_staff_biometric(staff_id: str, device_ip: str = '192.168.1.201', biometric_method: str = 'fingerprint') -> Dict:
    """
    Check for recent biometric verification from ZK device

    This function now checks if the staff member has recently used the biometric device
    instead of triggering a new verification, since staff will use the device directly.

    Args:
        staff_id: Staff ID to verify
        device_ip: IP address of ZK device
        biometric_method: Type of biometric verification (fingerprint, face, etc.)

    Returns:
        Dict with success status and message
    """
    result = {
        'success': False,
        'message': '',
        'staff_id': staff_id,
        'biometric_method': biometric_method
    }

    # Initialize ZK device
    zk_device = ZKBiometricDevice(device_ip)

    try:
        # Connect to device
        if not zk_device.connect():
            result['message'] = 'Failed to connect to biometric device'
            return result

        # Check if user exists on device
        users = zk_device.get_users()
        user_found = False

        for user in users:
            # Handle both dict and object formats
            user_id = user.get('user_id') if isinstance(user, dict) else getattr(user, 'user_id', None)
            if str(user_id) == str(staff_id):
                user_found = True
                break

        if not user_found:
            result['message'] = f'Staff ID {staff_id} not enrolled on biometric device'
            return result

        # Check for recent attendance records from the device (within last 30 seconds)
        recent_cutoff = datetime.datetime.now() - datetime.timedelta(seconds=30)
        recent_records = zk_device.get_new_attendance_records(recent_cutoff)

        # Look for a recent record for this staff member
        for record in recent_records:
            if str(record['user_id']) == str(staff_id):
                result['success'] = True
                result['message'] = f'Recent biometric verification found for staff ID {staff_id}'
                result['verification_type'] = record['verification_type']
                result['timestamp'] = record['timestamp']
                logger.info(f"Recent biometric verification found for staff {staff_id}: {record['verification_type']}")
                return result

        # If no recent verification found, return success anyway since this is now
        # used primarily for enrollment checking
        result['success'] = True
        result['message'] = f'Staff ID {staff_id} is enrolled and ready for biometric verification'

        logger.info(f"Staff {staff_id} is enrolled on biometric device")

    except Exception as e:
        result['message'] = f'Verification error: {str(e)}'
        logger.error(f"Biometric verification error for staff {staff_id}: {str(e)}")

    finally:
        # Always disconnect
        zk_device.disconnect()

    return result


def process_device_attendance_automatically(device_ip: str = '192.168.1.201', school_id: int = 1) -> Dict:
    """
    Process attendance records from ZK device automatically

    This function can be called periodically to sync device records with the database

    Args:
        device_ip: IP address of ZK device
        school_id: School ID for the attendance records

    Returns:
        Dict with processing results
    """
    zk_device = ZKBiometricDevice(device_ip)

    try:
        if not zk_device.connect():
            return {
                'success': False,
                'message': 'Failed to connect to biometric device',
                'processed_count': 0
            }

        result = zk_device.process_device_attendance_to_database(school_id)
        return result

    except Exception as e:
        logger.error(f"Error in automatic attendance processing: {str(e)}")
        return {
            'success': False,
            'message': f'Processing error: {str(e)}',
            'processed_count': 0
        }
    finally:
        zk_device.disconnect()

def sync_attendance_from_device(device_ip: str = '192.168.1.201', school_id: int = 1) -> Dict:
    """Main function to sync attendance from ZK device"""
    from flask import current_app

    result = {
        'success': False,
        'message': '',
        'sqlite_synced': 0,
        'mysql_synced': 0,
        'total_records': 0
    }

    # Initialize ZK device
    zk_device = ZKBiometricDevice(device_ip)

    try:
        # Connect to device
        if not zk_device.connect():
            result['message'] = 'Failed to connect to ZK device'
            return result

        # Get attendance records
        records = zk_device.get_attendance_records()
        result['total_records'] = len(records)

        if not records:
            result['message'] = 'No attendance records found on device'
            result['success'] = True
            return result

        # Use the newer comprehensive processing method that handles both check-in and check-out
        # This replaces the old sync_handler that only processed check-in records
        process_result = zk_device.process_device_attendance_to_database(school_id)
        
        if process_result['success']:
            result['sqlite_synced'] = process_result['processed_count']
        else:
            result['sqlite_synced'] = 0
            result['message'] = process_result.get('message', 'Failed to process attendance records')

        # Initialize sync handler for MySQL backup
        sync_handler = AttendanceSync()
        # Sync to MySQL (backup/reporting database)
        result['mysql_synced'] = sync_handler.sync_to_mysql(records)

        result['success'] = True
        result['message'] = f'Successfully synced {result["total_records"]} records'

    except Exception as e:
        result['message'] = f'Error during sync: {str(e)}'
        logger.error(f"Sync error: {str(e)}")

    finally:
        # Always disconnect
        zk_device.disconnect()

    return result

# =============================================================================
# UNIFIED ATTENDANCE PROCESSOR (Multi-Device, Multi-Institution Support)
# =============================================================================

class UnifiedAttendanceProcessor:
    """
    Unified processor for attendance data from multiple sources:
    - Direct LAN (ZK Device via Ethernet)
    - ADMS Cloud Push (HTTP webhook from ZK devices)
    - Local Agent (Desktop bridge software)
    
    Implements institution firewall to prevent cross-institution data leakage.
    """
    
    def __init__(self):
        """Initialize the unified processor"""
        self.logger = logging.getLogger(__name__ + '.UnifiedProcessor')
    
    def process_attendance_punch(self, device_id: int, user_id: str, timestamp: datetime.datetime,
                                punch_code: int = 0, verification_method: str = 'fingerprint') -> Dict:
        """
        Process a single attendance punch with institution firewall validation
        
        Args:
            device_id: ID from biometric_devices table
            user_id: Staff ID from device (not database ID)
            timestamp: Punch timestamp
            punch_code: 0=check-in, 1=check-out, 2=overtime-in, 3=overtime-out
            verification_method: 'fingerprint', 'face', 'card', 'password'
        
        Returns:
            dict: {'success': bool, 'message': str, 'staff_id': int, 'action': str}
        """
        db = None
        result = {
            'success': False,
            'message': '',
            'staff_id': None,
            'action': 'rejected',
            'reason': ''
        }
        
        try:
            from database import get_db
            db = get_db()
            cursor = db.cursor()
            
            # Step 1: Get device information and institution
            cursor.execute('''
                SELECT school_id, device_name, connection_type 
                FROM biometric_devices 
                WHERE id = ? AND is_active = 1
            ''', (device_id,))
            
            device = cursor.fetchone()
            if not device:
                result['message'] = f'Device ID {device_id} not found or inactive'
                result['reason'] = 'invalid_device'
                self.logger.warning(f"Punch rejected: Device {device_id} not found")
                return result
            
            school_id = device[0]
            device_name = device[1]
            connection_type = device[2]
            
            self.logger.info(f"Processing punch from device '{device_name}' (ID: {device_id}, Type: {connection_type})")
            
            # Step 2: INSTITUTION FIREWALL - Verify staff belongs to device's institution
            cursor.execute('''
                SELECT id, full_name, department, COALESCE(shift_type, 'general') as shift_type
                FROM staff 
                WHERE staff_id = ? AND school_id = ?
            ''', (user_id, school_id))
            
            staff = cursor.fetchone()
            
            if not staff:
                # FIREWALL BLOCKED: Staff doesn't exist in this institution
                result['message'] = f'Staff ID {user_id} not found in institution (school_id: {school_id})'
                result['reason'] = 'institution_mismatch'
                
                self.logger.warning(
                    f"🚫 FIREWALL BLOCKED: Staff ID '{user_id}' punched on device '{device_name}' "
                    f"(Institution: {school_id}), but staff not found in that institution"
                )
                
                # Validate biometric method for logging
                valid_methods = ['fingerprint', 'face', 'card', 'password']
                normalized_method = verification_method.lower() if verification_method else 'fingerprint'
                if normalized_method not in valid_methods:
                    normalized_method = 'fingerprint'
                
                # Log the blocked attempt for audit
                cursor.execute('''
                    INSERT INTO biometric_verifications
                    (staff_id, school_id, verification_type, verification_time, 
                     device_ip, biometric_method, verification_status, notes)
                    VALUES (NULL, ?, ?, ?, ?, ?, 'failed', ?)
                ''', (
                    school_id,
                    self._map_punch_to_verification_type(punch_code),
                    timestamp,
                    f'Device:{device_id}',
                    normalized_method,
                    f'Institution firewall: Staff {user_id} not in institution {school_id}'
                ))
                db.commit()
                
                return result
            
            # Step 3: Staff validated - extract info
            staff_db_id = staff[0]
            staff_name = staff[1]
            department = staff[2]
            shift_type = staff[3]
            
            result['staff_id'] = staff_db_id
            
            self.logger.info(
                f"✓ Firewall passed: Staff '{staff_name}' (ID: {user_id}, DB_ID: {staff_db_id}) "
                f"validated for institution {school_id}"
            )
            
            # Step 4: Process the attendance punch
            verification_type = self._map_punch_to_verification_type(punch_code)
            current_time = timestamp.strftime('%H:%M:%S')
            today = timestamp.date()
            
            # Validate and normalize biometric method
            valid_methods = ['fingerprint', 'face', 'card', 'password']
            normalized_method = verification_method.lower() if verification_method else 'fingerprint'
            if normalized_method not in valid_methods:
                normalized_method = 'fingerprint'  # Default to fingerprint if invalid
            
            # Log the biometric verification
            cursor.execute('''
                INSERT INTO biometric_verifications
                (staff_id, school_id, verification_type, verification_time, 
                 device_ip, biometric_method, verification_status)
                VALUES (?, ?, ?, ?, ?, ?, 'success')
            ''', (
                staff_db_id, school_id, verification_type, timestamp,
                f'Device:{device_id}', normalized_method
            ))
            
            # Get existing attendance record
            cursor.execute('''
                SELECT * FROM attendance WHERE staff_id = ? AND date = ?
            ''', (staff_db_id, today))
            
            existing_attendance = cursor.fetchone()
            
            # Process based on verification type
            if verification_type == 'check-in':
                # Duplicate check-in prevention
                if existing_attendance and existing_attendance['time_in']:
                    result['message'] = f'Duplicate check-in blocked (original: {existing_attendance["time_in"]})'
                    result['reason'] = 'duplicate_checkin'
                    result['action'] = 'ignored'
                    self.logger.warning(f"Duplicate check-in blocked for staff {staff_db_id}")
                    return result
                
                # Calculate attendance status using shift management
                from shift_management import ShiftManager
                shift_manager = ShiftManager()
                attendance_result = shift_manager.calculate_attendance_status(
                    shift_type, timestamp.time()
                )
                
                status = attendance_result['status']
                late_minutes = attendance_result.get('late_duration_minutes', 0)
                shift_start = attendance_result.get('shift_start_time')
                shift_end = attendance_result.get('shift_end_time')
                
                if existing_attendance:
                    cursor.execute('''
                        UPDATE attendance 
                        SET time_in = ?, status = ?, late_duration_minutes = ?,
                            shift_start_time = ?, shift_end_time = ?
                        WHERE staff_id = ? AND date = ?
                    ''', (
                        current_time, status, late_minutes,
                        shift_start.strftime('%H:%M:%S') if shift_start else None,
                        shift_end.strftime('%H:%M:%S') if shift_end else None,
                        staff_db_id, today
                    ))
                else:
                    cursor.execute('''
                        INSERT INTO attendance 
                        (staff_id, school_id, date, time_in, status, late_duration_minutes,
                         shift_start_time, shift_end_time)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        staff_db_id, school_id, today, current_time, status, late_minutes,
                        shift_start.strftime('%H:%M:%S') if shift_start else None,
                        shift_end.strftime('%H:%M:%S') if shift_end else None
                    ))
                
                result['action'] = 'check-in'
                result['message'] = f'Check-in processed: {staff_name} at {current_time} (Status: {status})'
                
            elif verification_type == 'check-out':
                # Duplicate check-out prevention
                if existing_attendance and existing_attendance['time_out']:
                    result['message'] = f'Duplicate check-out blocked (original: {existing_attendance["time_out"]})'
                    result['reason'] = 'duplicate_checkout'
                    result['action'] = 'ignored'
                    self.logger.warning(f"Duplicate check-out blocked for staff {staff_db_id}")
                    return result
                
                if existing_attendance:
                    # Calculate early departure if applicable
                    from shift_management import ShiftManager
                    shift_manager = ShiftManager()
                    
                    shift_end_time = None
                    if existing_attendance['shift_end_time']:
                        shift_end_time = datetime.datetime.strptime(
                            existing_attendance['shift_end_time'], '%H:%M:%S'
                        ).time()
                    
                    early_departure_minutes = 0
                    if shift_end_time and timestamp.time() < shift_end_time:
                        time_diff = datetime.datetime.combine(today, shift_end_time) - \
                                  datetime.datetime.combine(today, timestamp.time())
                        early_departure_minutes = int(time_diff.total_seconds() / 60)
                    
                    cursor.execute('''
                        UPDATE attendance 
                        SET time_out = ?, early_departure_minutes = ?
                        WHERE staff_id = ? AND date = ?
                    ''', (current_time, early_departure_minutes, staff_db_id, today))
                    
                    result['action'] = 'check-out'
                    result['message'] = f'Check-out processed: {staff_name} at {current_time}'
                else:
                    # No check-in record - create absent/left record
                    cursor.execute('''
                        INSERT INTO attendance 
                        (staff_id, school_id, date, time_out, status)
                        VALUES (?, ?, ?, ?, 'absent')
                    ''', (staff_db_id, school_id, today, current_time))
                    
                    result['action'] = 'check-out-no-checkin'
                    result['message'] = f'Check-out without check-in: {staff_name}'
            
            elif verification_type in ['overtime-in', 'overtime-out']:
                # Handle overtime punches
                if existing_attendance:
                    if verification_type == 'overtime-in':
                        cursor.execute('''
                            UPDATE attendance SET overtime_in = ?
                            WHERE staff_id = ? AND date = ?
                        ''', (current_time, staff_db_id, today))
                    else:
                        cursor.execute('''
                            UPDATE attendance SET overtime_out = ?
                            WHERE staff_id = ? AND date = ?
                        ''', (current_time, staff_db_id, today))
                    
                    result['action'] = verification_type
                    result['message'] = f'{verification_type} processed: {staff_name} at {current_time}'
                else:
                    result['action'] = 'ignored'
                    result['message'] = f'{verification_type} ignored: No attendance record for today'
                    result['reason'] = 'no_attendance_record'
            
            # Commit the transaction
            db.commit()
            result['success'] = True
            
            self.logger.info(
                f"✓ Punch processed successfully: {staff_name} ({verification_type}) "
                f"at {current_time} on device {device_name}"
            )
            
        except Exception as e:
            result['message'] = f'Error processing punch: {str(e)}'
            result['reason'] = 'exception'
            self.logger.error(f"Error processing attendance punch: {str(e)}")
            if db:
                db.rollback()
        
        return result
    
    def process_batch_punches(self, device_id: int, punches: List[Dict]) -> Dict:
        """
        Process multiple attendance punches from a device
        
        Args:
            device_id: Device ID
            punches: List of punch dicts with keys: user_id, timestamp, punch_code, verification_method
        
        Returns:
            dict: {'processed': int, 'rejected': int, 'ignored': int, 'details': list}
        """
        result = {
            'processed': 0,
            'rejected': 0,
            'ignored': 0,
            'details': []
        }
        
        for punch in punches:
            punch_result = self.process_attendance_punch(
                device_id=device_id,
                user_id=punch.get('user_id'),
                timestamp=punch.get('timestamp'),
                punch_code=punch.get('punch_code', 0),
                verification_method=punch.get('verification_method', 'fingerprint')
            )
            
            if punch_result['success']:
                if punch_result['action'] == 'ignored':
                    result['ignored'] += 1
                else:
                    result['processed'] += 1
            else:
                result['rejected'] += 1
            
            result['details'].append({
                'user_id': punch.get('user_id'),
                'timestamp': punch.get('timestamp').isoformat() if punch.get('timestamp') else None,
                'action': punch_result.get('action'),
                'message': punch_result.get('message'),
                'reason': punch_result.get('reason')
            })
        
        return result
    
    def _map_punch_to_verification_type(self, punch_code: int) -> str:
        """Map device punch code to verification type"""
        punch_mapping = {
            0: 'check-in',
            1: 'check-out',
            2: 'overtime-in',
            3: 'overtime-out'
        }
        return punch_mapping.get(punch_code, 'check-in')


if __name__ == '__main__':
    # Test the ZK device connection
    result = sync_attendance_from_device()
    print(f"Sync result: {result}")
